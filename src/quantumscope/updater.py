"""Checking for and downloading QuantumScope updates (Qt-free).

Nothing here runs unless the user asks: the GUI asks for permission first, then calls
`check()`, which makes one request to GitHub's public releases list. Only full releases
are offered (drafts and pre-releases are skipped). Downloads are verified against the
release's SHA-256 checksum file before anything is opened, and a mismatching file is
deleted.
"""
from dataclasses import dataclass
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

REPOSITORY = 'Onimee58/QuantumScope'
RELEASES_URL = f'https://api.github.com/repos/{REPOSITORY}/releases?per_page=30'
TIMEOUT = 15
CHUNK = 1 << 16


class UpdateError(Exception):
    """A problem the user should see in plain words."""


@dataclass(frozen=True)
class Release:
    version: tuple
    tag: str
    notes: str
    page: str
    installer: dict = None          # {'name', 'url', 'size'} for this system, or None
    checksum_url: str = ''          # the installer's .sha256 file

    @property
    def label(self):
        return '.'.join(map(str, self.version))


def parse_version(text):
    """'v0.6.2' → (0, 6, 2); None for anything that is not a plain release number."""
    match = re.fullmatch(r'v?(\d+)\.(\d+)(?:\.(\d+))?', str(text).strip())
    if not match:
        return None
    return tuple(int(x) for x in match.groups(default='0'))


def platform_key(platform=None):
    platform = platform or sys.platform
    if platform.startswith('win'):
        return 'windows'
    if platform == 'darwin':
        return 'macos'
    return 'linux'


INSTALLER_PATTERNS = {
    'windows': re.compile(r'^QuantumScope-[\d.]+-Setup\.exe$'),
    'macos': re.compile(r'^QuantumScope-[\d.]+-macOS\.dmg$'),
    'linux': re.compile(r'^quantumscope_[\d.]+_amd64\.deb$'),
}


def latest(releases, current, platform=None):
    """The newest full release newer than `current`, with this system's installer; or None."""
    key = platform_key(platform)
    best = None
    for item in releases:
        if not isinstance(item, dict) or item.get('draft') or item.get('prerelease'):
            continue                                   # pre-releases are never offered
        version = parse_version(item.get('tag_name', ''))
        if version is None or version <= current or (best and version <= best.version):
            continue
        assets = {a.get('name'): a for a in item.get('assets', []) if isinstance(a, dict)}
        installer = next((a for name, a in assets.items() if name and INSTALLER_PATTERNS[key].match(name)), None)
        checksum = assets.get(f'{installer["name"]}.sha256') if installer else None
        best = Release(version, item.get('tag_name', ''), item.get('body') or '', item.get('html_url', ''),
                       {'name': installer['name'], 'url': installer.get('browser_download_url', ''),
                        'size': installer.get('size', 0)} if installer else None,
                       checksum.get('browser_download_url', '') if checksum else '')
    return best


def _request(url, opener=None):
    request = urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json',
                                                   'User-Agent': 'QuantumScope-updater'})
    try:
        return (opener or urllib.request.urlopen)(request, timeout=TIMEOUT)
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429) and exc.headers.get('X-RateLimit-Remaining') == '0':
            reset = exc.headers.get('X-RateLimit-Reset')
            minutes = max(1, round((int(reset) - time.time()) / 60)) if reset and reset.isdigit() else None
            wait = f' Try again in about {minutes} minute{"s" if minutes != 1 else ""}.' if minutes else ' Try again later.'
            raise UpdateError('GitHub limits how often a network can check for updates, and that limit has '
                              'been reached (common on shared university networks).' + wait) from exc
        raise UpdateError(f'GitHub answered with an error ({exc.code}). Try again later.') from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise UpdateError('Could not reach GitHub. Check your internet connection and try again.') from exc


def check(current, platform=None, opener=None):
    """One request to GitHub: the newest full release newer than `current`, or None."""
    with _request(RELEASES_URL, opener) as response:
        try:
            releases = json.loads(response.read().decode('utf-8'))
        except (ValueError, UnicodeDecodeError) as exc:
            raise UpdateError('GitHub sent an answer QuantumScope could not read.') from exc
    if not isinstance(releases, list):
        raise UpdateError('GitHub sent an unexpected answer.')
    return latest(releases, current, platform)


def parse_checksum(text, filename):
    """The SHA-256 for `filename` from a 'hash  name' line (sha256sum format)."""
    for line in str(text).splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[-1].lstrip('*') == filename and re.fullmatch(r'[0-9a-fA-F]{64}', parts[0]):
            return parts[0].lower()
        if len(parts) == 1 and re.fullmatch(r'[0-9a-fA-F]{64}', parts[0]):
            return parts[0].lower()
    raise UpdateError('The release has no valid checksum for this installer, so it will not be installed.')


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b''):
            digest.update(chunk)
    return digest.hexdigest()


def download(release, folder, progress=None, opener=None):
    """Download the installer and its checksum; verify; return the installer's path.

    progress(done, total) may return False to cancel. A file that fails verification is
    deleted and never returned.
    """
    if not release.installer:
        raise UpdateError('This release has no installer for your system.')
    if not release.checksum_url:
        raise UpdateError('This release has no checksum file for its installer, so it will not be installed.')
    with _request(release.checksum_url, opener) as response:
        expected = parse_checksum(response.read().decode('utf-8', 'replace'), release.installer['name'])
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, release.installer['name'])
    partial = path + '.part'
    try:
        with _request(release.installer['url'], opener) as response, open(partial, 'wb') as out:
            total = int(response.headers.get('Content-Length') or release.installer.get('size') or 0)
            done = 0
            while True:
                chunk = response.read(CHUNK)
                if not chunk:
                    break
                out.write(chunk)
                done += len(chunk)
                if progress is not None and progress(done, total) is False:
                    raise UpdateError('Download cancelled.')
        if sha256_of(partial) != expected:
            raise UpdateError('The downloaded file does not match the release checksum, so it was deleted. '
                              'Try again later, or download the installer from the release page.')
        os.replace(partial, path)
        return path
    finally:
        if os.path.exists(partial):
            os.remove(partial)


def install_plan(path, platform=None, frozen=None):
    """How to install a verified download: (kind, command or None, message for the user)."""
    key = platform_key(platform)
    frozen = getattr(sys, 'frozen', False) if frozen is None else frozen
    if not frozen:
        return ('source', None, 'This copy of QuantumScope runs from source. Update it with:\n\n'
                                '    git pull\n\nin the QuantumScope folder (then restart).')
    if key == 'windows':
        return ('run', [path], 'QuantumScope will close and the installer will start.')
    if key == 'macos':
        return ('open', ['open', path], 'The installer will open: drag QuantumScope to Applications, '
                                        'replacing the old version, then start it again.')
    return ('run', ['pkexec', 'apt-get', 'install', '-y', path],
            'Ubuntu will ask for your password to install the update. Restart QuantumScope afterwards.')
