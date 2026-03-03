from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Tuple
import os, re, shutil, tarfile, tempfile, time, ssl
from urllib import request, error as urlerror
from ..utils.system import Color, console, error
from ..utils.sub_process import execute_piped
from ..util import get_file_size_str, get_time_str

if TYPE_CHECKING:
    from ..build_dependency import BuildDependency
    from ..types.git import Git

# Cache token for later
_cached_github_token: Optional[str] = None
_cached_github_token_checked = False

# Tries to find github token from 3 places:
# env: GITHUB_TOKEN, GH_TOKEN
# `gh auth token` command if its installed and authenticated
def _get_github_token() -> Optional[str]:
    global _cached_github_token, _cached_github_token_checked
    if _cached_github_token_checked:
        return _cached_github_token
    _cached_github_token_checked = True

    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if token:
        _cached_github_token = token.strip()
        return _cached_github_token

    # Make sure program is installed
    if not shutil.which('gh'):
        return None

    # Make sure user is authenticated
    try:
        status = execute_piped('gh auth status', timeout=5)
        if not status or 'Logged in' not in status:
            return None
    except Exception:
        return None

    try:
        result = execute_piped('gh auth token', timeout=5)
        if result and result.strip():
            _cached_github_token = result.strip()
            return _cached_github_token
    except Exception:
        pass

    return None

# Parses url to a github owner/repo
def parse_github_url(url: str) -> Optional[Tuple[str, str]]:
    m = re.match(r'^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$', url)
    if m:
        return m.group(1), m.group(2)

    m = re.match(r'^https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$', url)
    if m:
        return m.group(1), m.group(2)

    return None


def get_tarball_url(owner: str, repo: str, ref: str) -> str:
    return f'https://api.github.com/repos/{owner}/{repo}/tarball/{ref}'


def get_tarball_ref(git: Git) -> str:
    if git.tag:
        return git.tag
    if git.branch:
        return git.branch
    return 'HEAD'


def download_and_extract_tarball(dep: BuildDependency, git: Git) -> bool:
    parsed = parse_github_url(git.url)
    if not parsed:
        return False

    owner, repo = parsed
    ref = get_tarball_ref(git)
    tarball_url = get_tarball_url(owner, repo, ref)

    if dep.config.print:
        console(f'  - Target {dep.name: <16} TARBALL downloading {owner}/{repo}@{ref}', color=Color.BLUE)

    if dep.config.verbose:
        console(f'    {dep.name}  tarball URL: {tarball_url}', color=Color.YELLOW)

    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_OPTIONAL

        start = time.time()

        # Download to a temporary file
        tmp_dir = tempfile.gettempdir()
        safe_ref = ref.replace('/', '_')
        tmp_file = os.path.join(tmp_dir, f'mama_{dep.name}_{safe_ref}.tar.gz')

        req = request.Request(tarball_url, headers={
            'Accept': 'application/vnd.github+json',
        })

        token = _get_github_token()
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        elif dep.config.verbose:
            console(f'    {dep.name}  no github token found, using unauthenticated request', color=Color.YELLOW)

        with request.urlopen(req, context=ctx, timeout=60) as response:
            size = response.info().get('Content-Length')
            size = int(size.strip()) if size else None

            if dep.config.print and size:
                console(f'    {dep.name}  downloading {get_file_size_str(size)}')

            with open(tmp_file, 'wb') as f:
                transferred = 0
                while True:
                    chunk = response.read(64 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    transferred += len(chunk)

        elapsed = time.time() - start

        if dep.config.verbose:
            console(f'    {dep.name}  downloaded {get_file_size_str(transferred)} in {get_time_str(elapsed)}', color=Color.YELLOW)

        # Ensure source directory exists
        os.makedirs(dep.src_dir, exist_ok=True)

        # github tarballs have a top-level directory like "repo-ref/"
        # We need to strip that and extract contents directly into src_dir
        _extract_tarball_stripped(tmp_file, dep.src_dir, dep.config.verbose, dep.name)

        # Clean up temp file
        try:
            os.remove(tmp_file)
        except OSError:
            pass

        elapsed = time.time() - start
        if dep.config.print:
            console(f'  - Target {dep.name: <16} TARBALL done ({get_time_str(elapsed)})', color=Color.BLUE)

        return True

    except urlerror.HTTPError as e:
        if dep.config.print:
            error(f'  - Target {dep.name: <16} TARBALL HTTP error {e.code}: {e.reason} for {tarball_url}')
        return False
    except Exception as e:
        if dep.config.print:
            error(f'  - Target {dep.name: <16} TARBALL failed: {e}')
        return False


def _extract_tarball_stripped(tarball_path: str, dest_dir: str, verbose: bool, name: str):
    with tarfile.open(tarball_path, 'r:gz') as tar:
        # Find the common prefix (top-level directory)
        members = tar.getmembers()
        if not members:
            raise RuntimeError(f'Tarball for {name} is empty')

        # The first member is typically the top-level directory
        prefix = members[0].name
        if not prefix.endswith('/'):
            # Find common prefix from all members
            prefix = os.path.commonprefix([m.name for m in members])
            prefix = prefix.split('/')[0] + '/'

        if verbose:
            console(f'    {name}  extracting {len(members)} entries, stripping prefix "{prefix}"')

        # Extract all members with the prefix stripped
        for member in members:
            if not member.name.startswith(prefix):
                continue

            # Strip the prefix
            member_path = member.name[len(prefix):]
            if not member_path:
                continue  # Skip the top-level directory itself

            # Set the new path
            member.name = member_path

            # Security check: prevent path traversal
            abs_path = os.path.normpath(os.path.join(dest_dir, member_path))
            if not abs_path.startswith(os.path.normpath(dest_dir)):
                continue

            tar.extract(member, dest_dir)
