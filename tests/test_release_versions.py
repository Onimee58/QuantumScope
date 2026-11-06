"""Every place that states QuantumScope's version agrees, and the release workflow states none itself.

v0.8.0's first build named and versioned its installers 0.7.8, because the version was typed into
the workflow by hand. The workflow now reads it from the code and refuses a tag that does not match.
"""
import os
import re

ROOT = os.path.join(os.path.dirname(__file__), '..')


def read(*parts):
    return open(os.path.join(ROOT, *parts), encoding='utf-8').read()


def test_all_version_declarations_agree():
    version = re.search(r'__version__ = "([^"]+)"', read('src', 'quantumscope', '__init__.py')).group(1)
    assert re.search(r'^version = "([^"]+)"', read('pyproject.toml'), re.M).group(1) == version
    assert re.search(r'#define MyAppVersion "([^"]+)"', read('packaging', 'QuantumScope.iss')).group(1) == version
    assert re.search(r'VERSION="\$\{1:-([^}]+)\}"', read('packaging', 'build_deb.sh')).group(1) == version
    assert f'version-v{version}-' in read('README.md') and read('CHANGELOG.md').startswith(f'## v{version} ')


def test_the_release_workflow_reads_the_version_and_checks_the_tag():
    workflow = read('.github', 'workflows', 'release.yml')
    assert not re.search(r'(?<![\w.])\d+\.\d+\.\d+(?![\w.])', workflow), 'no hand-written version numbers'
    assert "open('src/quantumscope/__init__.py')" in workflow and 'GITHUB_ENV' in workflow
    assert '"$GITHUB_REF_NAME" != "v$VERSION"' in workflow and 'exit 1' in workflow
    for use in ('build_deb.sh "$VERSION"', '/DMyAppVersion=$env:VERSION', 'QuantumScope-$VERSION-macOS.dmg',
                'QuantumScope-${{ env.VERSION }}-'):
        assert use in workflow, use
