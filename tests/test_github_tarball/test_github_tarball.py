import os
from testutils import init, shell_exec, file_contains, file_exists

src_tag = 'packages/ExampleRemote/ExampleRemote'
src_commit = 'packages/ExampleRemote2/ExampleRemote2'
src_branch = 'packages/ExampleRemote3/ExampleRemote3'
# Test downloading tarballs from github
def stage1():
    os.environ['MAMA_ENABLE_TARBALL'] = '1'
    shell_exec('mama build')

    assert file_exists(f'{src_tag}/remote.h'), 'Tag pinned dep missing remote.h'
    assert file_contains(f'{src_tag}/remote.h', 'REMOTE_VERSION 2'), 'Tag pin fetched wrong version'
    assert file_exists(f'{src_commit}/remote.h'), 'Commit pinned dep missing remote.h'
    assert file_contains(f'{src_commit}/remote.h', 'REMOTE_VERSION 2'), 'Commit pin fetched wrong version'
    assert file_exists(f'{src_branch}/remote.h'), 'Branch pinned dep missing remote.h'

    assert not os.path.exists(f'{src_tag}/.git'), 'Tarball should not have .git directory'
    assert not os.path.exists(f'{src_commit}/.git'), 'Tarball should not have .git directory'
    assert not os.path.exists(f'{src_branch}/.git'), 'Tarball should not have .git directory'

# Test going from tarball to git clone
def stage2():
    os.environ['MAMA_ENABLE_TARBALL'] = '0'
    shell_exec('mama update all')

    assert os.path.exists(f'{src_tag}/.git'), 'Git clone should create .git directory'
    assert os.path.exists(f'{src_commit}/.git'), 'Git clone should create .git directory'
    assert os.path.exists(f'{src_branch}/.git'), 'Git clone should create .git directory'

# Test going from git clone back to tarball
def stage3():
    os.environ['MAMA_ENABLE_TARBALL'] = '1'
    shell_exec('mama update all')

    assert not os.path.exists(f'{src_tag}/.git'), 'Tarball should not have .git directory after switching back'
    assert not os.path.exists(f'{src_commit}/.git'), 'Tarball should not have .git directory after switching back'
    assert not os.path.exists(f'{src_branch}/.git'), 'Tarball should not have .git directory after switching back'

def test_github_tarball():
    init(__file__, clean_dirs=['packages'])

    stage1()
    stage2()
    stage3()

