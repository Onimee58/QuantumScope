"""v0.7.8: the user guide (docs/user-guide.md → assets/QuantumScope-User-Guide.pdf)."""
import os
import re

from importlib.resources import files

ROOT = os.path.join(os.path.dirname(__file__), '..')
GUIDE = os.path.join(ROOT, 'docs', 'user-guide.md')


def test_the_guide_source_and_its_screenshots():
    text = open(GUIDE, encoding='utf-8').read()
    for chapter in ('Installing and updating', 'A tour of the window', 'Hydrogen', 'Quantum Principles',
                    'Quantum Circuits', 'Quantum ML', 'Learn', 'Settings', 'Troubleshooting',
                    'Mouse and keyboard reference'):
        assert re.search(rf'^## \d+\. {re.escape(chapter)}$', text, re.M), chapter
    images = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', text)
    assert len(images) >= 10
    for image in images:
        assert os.path.isfile(os.path.join(ROOT, 'docs', image)), image


def test_the_pdf_ships_with_the_package():
    guide = files('quantumscope').joinpath('assets/QuantumScope-User-Guide.pdf')
    data = guide.read_bytes()
    assert data[:5] == b'%PDF-' and len(data) > 200_000                     # text and screenshots


def test_the_guide_names_controls_that_exist():
    """A few control names the guide relies on, checked against the source."""
    text = open(GUIDE, encoding='utf-8').read()
    source = ''
    for folder, _, names in os.walk(os.path.join(ROOT, 'src', 'quantumscope', 'gui')):
        for name in names:
            if name.endswith('.py'):
                source += open(os.path.join(folder, name), encoding='utf-8').read()
    # Algorithm parameters (such as VQLS's "Your own system") are labelled in the physics package.
    source += open(os.path.join(ROOT, 'src', 'quantumscope', 'physics', 'algorithms.py'), encoding='utf-8').read()
    for control in ('Check for updates…', 'Run shots', 'Verify / truth table', 'Randomize all', 'Landscape…',
                    'Fire particles', 'Measure once', 'Measure many', 'Send one pair', 'Run Bell test',
                    'Teleport many', 'Open in the circuit simulator', 'Export PDF…', 'My course folder…',
                    'Restore defaults', 'Render state', 'Enable second 3D viewer', 'Simplify circuit…',
                    'Import CSV or .npz…', 'Apply suggestions', 'Qubits (= features)', 'Samples per class',
                    'PCA components', 'Shots per entry', 'Trainable layers', 'Open in circuit simulator',
                    'Show the solution', 'Your own system'):
        assert control in text, control
        assert control in source, control
