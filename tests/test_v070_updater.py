"""v0.7.0 (9a): the opt-in updater, tested against a simulated GitHub."""
import hashlib
import io
import json
import os
import time
import urllib.error

import pytest

from quantumscope import updater

INSTALLER = b'pretend installer bytes ' * 1000


class Response(io.BytesIO):
    def __init__(self, data, headers=None):
        super().__init__(data)
        self.headers = headers or {'Content-Length': str(len(data))}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


def release(tag, prerelease=False, draft=False, assets=None, body='Notes'):
    return {'tag_name': tag, 'prerelease': prerelease, 'draft': draft, 'body': body,
            'html_url': f'https://github.com/x/releases/{tag}', 'assets': assets if assets is not None else [
                {'name': f'QuantumScope-{tag[1:]}-Setup.exe', 'browser_download_url': f'https://dl/{tag}/setup.exe',
                 'size': len(INSTALLER)},
                {'name': f'QuantumScope-{tag[1:]}-Setup.exe.sha256', 'browser_download_url': f'https://dl/{tag}/setup.sha'},
                {'name': f'QuantumScope-{tag[1:]}-macOS.dmg', 'browser_download_url': f'https://dl/{tag}/mac.dmg'},
                {'name': f'quantumscope_{tag[1:]}_amd64.deb', 'browser_download_url': f'https://dl/{tag}/linux.deb'},
                {'name': f'quantumscope_{tag[1:]}_amd64.deb.sha256', 'browser_download_url': f'https://dl/{tag}/linux.sha'}]}


RELEASES = [release('v0.8.0', prerelease=True), release('v0.7.1', draft=True), release('v0.7.0'),
            release('v0.6.2'), release('nightly')]


def github(releases=RELEASES, checksum=None, installer=INSTALLER):
    # The checksum always describes the genuine installer; `installer` is what is actually served
    # (pass altered bytes to model a tampered or corrupted download).
    digest = checksum or hashlib.sha256(INSTALLER).hexdigest()

    def opener(request, timeout=None):
        url = request.full_url
        if 'api.github.com' in url:
            return Response(json.dumps(releases).encode())
        if url.endswith('.sha'):                   # a checksum file: "<sha256>  <installer name>"
            name = {'setup.sha': 'Setup.exe', 'linux.sha': 'amd64.deb'}[url.split('/')[-1]]
            tag = url.split('/')[-2][1:]
            installer_name = f'QuantumScope-{tag}-Setup.exe' if name == 'Setup.exe' else f'quantumscope_{tag}_amd64.deb'
            return Response(f'{digest}  {installer_name}\n'.encode())
        return Response(installer)
    return opener


def test_versions():
    assert updater.parse_version('v0.6.2') == (0, 6, 2) and updater.parse_version('1.0') == (1, 0, 0)
    assert updater.parse_version('v0.7.0-rc1') is None and updater.parse_version('nightly') is None
    assert (0, 6, 10) > (0, 6, 2)


@pytest.mark.parametrize('platform,name', [('win32', 'QuantumScope-0.7.0-Setup.exe'),
                                           ('darwin', 'QuantumScope-0.7.0-macOS.dmg'),
                                           ('linux', 'quantumscope_0.7.0_amd64.deb')])
def test_newest_full_release_for_each_platform(platform, name):
    found = updater.latest(RELEASES, (0, 6, 2), platform)
    assert found.label == '0.7.0' and found.installer['name'] == name    # pre-release 0.8.0 and draft 0.7.1 skipped
    assert bool(found.checksum_url) == (platform != 'darwin')            # this fake mac asset has no checksum


def test_up_to_date_and_older():
    assert updater.latest(RELEASES, (0, 7, 0), 'linux') is None
    assert updater.latest(RELEASES, (0, 9, 0), 'linux') is None


def test_check_uses_one_request():
    calls = []
    opener = github()
    found = updater.check((0, 6, 2), 'win32', lambda r, timeout=None: calls.append(r.full_url) or opener(r, timeout))
    assert found.label == '0.7.0' and calls == [updater.RELEASES_URL]


def test_rate_limit_message():
    def limited(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, 403, 'rate limited',
                                     {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': str(int(time.time()) + 1500)}, None)
    with pytest.raises(updater.UpdateError, match=r'limit .*about 25 minutes'):
        updater.check((0, 6, 2), 'linux', limited)


def test_offline_message():
    def offline(request, timeout=None):
        raise urllib.error.URLError('no network')
    with pytest.raises(updater.UpdateError, match='Could not reach GitHub'):
        updater.check((0, 6, 2), 'linux', offline)


def test_download_verifies_the_checksum(tmp_path):
    found = updater.latest(RELEASES, (0, 6, 2), 'win32')
    path = updater.download(found, str(tmp_path), opener=github())
    assert open(path, 'rb').read() == INSTALLER and os.listdir(tmp_path) == ['QuantumScope-0.7.0-Setup.exe']


def test_tampered_download_is_deleted(tmp_path):
    found = updater.latest(RELEASES, (0, 6, 2), 'win32')
    with pytest.raises(updater.UpdateError, match='does not match'):
        updater.download(found, str(tmp_path), opener=github(installer=b'tampered!'))
    assert os.listdir(tmp_path) == []


def test_missing_checksum_and_cancel(tmp_path):
    mac = updater.latest(RELEASES, (0, 6, 2), 'darwin')
    with pytest.raises(updater.UpdateError, match='no checksum'):
        updater.download(mac, str(tmp_path), opener=github())
    found = updater.latest(RELEASES, (0, 6, 2), 'linux')
    with pytest.raises(updater.UpdateError, match='cancelled'):
        updater.download(found, str(tmp_path), progress=lambda done, total: False, opener=github())
    assert os.listdir(tmp_path) == []


def test_checksum_parsing():
    h = 'a' * 64
    assert updater.parse_checksum(f'{h}  file.exe\n', 'file.exe') == h
    assert updater.parse_checksum(f'{h} *file.exe', 'file.exe') == h and updater.parse_checksum(h, 'x') == h
    with pytest.raises(updater.UpdateError):
        updater.parse_checksum('nonsense', 'file.exe')


def test_install_plans():
    assert updater.install_plan('x', 'linux', frozen=False)[0] == 'source'
    assert updater.install_plan('/tmp/q.exe', 'win32', frozen=True)[1] == ['/tmp/q.exe']
    assert updater.install_plan('/tmp/q.dmg', 'darwin', frozen=True)[1][0] == 'open'
    assert updater.install_plan('/tmp/q.deb', 'linux', frozen=True)[1][:2] == ['pkexec', 'apt-get']


def test_release_workflow_publishes_checksums():
    text = open('.github/workflows/release.yml').read()
    assert 'Write SHA-256 checksums next to the installers' in text and ".sha256" in text
    assert text.index('Write SHA-256 checksums') < text.index('Publish installers with tagged release')


@pytest.mark.skipif(os.environ.get('QUANTUMSCOPE_NETWORK_TESTS') != '1', reason='network tests are opt-in')
def test_live_github_release_list():
    found = updater.check((0, 0, 1), 'linux')
    assert found is not None and found.version >= (0, 6, 2)
