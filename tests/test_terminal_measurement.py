import pytest
from quantumscope.physics.circuits import Gate
from quantumscope.physics.circuit_files import (to_native_measured,from_native_measured,to_qasm_measured,from_qasm_measured,convert)

def test_terminal_measurement_file_and_qasm_roundtrip():
    ops=[Gate('H',(0,)),Gate('CX',(0,1))]
    native=to_native_measured(2,ops,[0,1])
    assert from_native_measured(native)==(2,ops,[0,1])
    qasm=to_qasm_measured(2,ops,[0,1])
    assert 'creg c[2];' in qasm
    assert 'measure q[0] -> c[0];' in qasm
    assert from_qasm_measured(qasm)==(2,ops,[0,1])
    assert from_native_measured(convert(qasm,'qasm'))==(2,ops,[0,1])
    assert from_qasm_measured(convert(native,'qscope'))==(2,ops,[0,1])

def test_measurement_rejects_mid_circuit_and_unsupported_mapping():
    pre='OPENQASM 2.0; qreg q[2]; creg c[2];'
    with pytest.raises(ValueError,match='after measurement'):
        from_qasm_measured(pre+'measure q[0] -> c[0]; x q[1];')
    with pytest.raises(ValueError,match='matching'):
        from_qasm_measured(pre+'measure q[0] -> c[1];')
    with pytest.raises(ValueError,match='indices'):
        to_native_measured(2,[],[2])

def test_legacy_native_backward_compatible():
    from quantumscope.physics.circuit_files import to_native
    assert from_native_measured(to_native(2,[Gate('X',(0,))]))==(2,[Gate('X',(0,))],[])
