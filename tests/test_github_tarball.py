from mama.utils.github_tarball import parse_github_url, get_tarball_url


def test_parse_github_ssh_url():
    assert parse_github_url('git@github.com:BatteredBunny/MamaExampleRemote.git') == ('BatteredBunny', 'MamaExampleRemote')
    assert parse_github_url('git@github.com:qcoro/qcoro.git') == ('qcoro', 'qcoro')
    assert parse_github_url('git@github.com:RedFox20/ReCpp.git') == ('RedFox20', 'ReCpp')


def test_parse_github_https_url():
    assert parse_github_url('https://github.com/RedFox20/ReCpp.git') == ('RedFox20', 'ReCpp')
    assert parse_github_url('https://github.com/RedFox20/ReCpp') == ('RedFox20', 'ReCpp')
    assert parse_github_url('https://github.com/libsdl-org/sdl.git') == ('libsdl-org', 'sdl')


def test_parse_non_github_url_returns_none():
    assert parse_github_url('git@bitbucket.org:user/repo.git') is None
    assert parse_github_url('https://gitlab.com/user/repo.git') is None
    assert parse_github_url('') is None
    assert parse_github_url('not-a-url') is None


def test_get_tarball_url():
    assert get_tarball_url('BatteredBunny', 'MamaExampleRemote', 'master') == \
        'https://api.github.com/repos/BatteredBunny/MamaExampleRemote/tarball/master'
    assert get_tarball_url('qcoro', 'qcoro', '98f23d8') == \
        'https://api.github.com/repos/qcoro/qcoro/tarball/98f23d8'
    assert get_tarball_url('libsdl-org', 'sdl', 'v3.4.2') == \
        'https://api.github.com/repos/libsdl-org/sdl/tarball/v3.4.2'
