import math
import pytest
from quantumscope.physics.circuits import Gate,evolution,distribution
from quantumscope.physics.circuit_files import to_native,from_native,to_qasm,from_qasm,convert

def test_roundtrip_native_qasm():
    gates=[Gate('H',(0,)),Gate('CX',(0,1)),Gate('RZ',(1,),math.pi/7),Gate('SWAP',(0,1))]
    n,restored=from_native(to_native(2,gates))
    assert n==2 and restored==gates
    n,restored=from_qasm(to_qasm(n,restored))
    assert n==2 and restored[0:2]==gates[0:2]
    assert abs(restored[2].angle-gates[2].angle)<1e-14
    assert max(abs(evolution(2,gates)[-1]-evolution(2,restored)[-1]))<1e-12

def test_qasm_conversion_and_rejection():
    source='OPENQASM 2.0; include "qelib1.inc"; qreg q[2]; h q[0]; cx q[0],q[1];'
    native=convert(source,'qasm');out=convert(native,'qscope')
    assert 'cx q[0],q[1];' in out
    assert list(distribution(evolution(*from_native(native))[-1]).round(5))==[.5,0,0,.5]
    with pytest.raises(ValueError):from_qasm(source+'creg c[2]; measure q[0] -> c[0];')
    with pytest.raises(ValueError):from_native('{"format":"wrong","schema_version":1,"qubits":2,"operations":[]}')
    with pytest.raises(ValueError):from_native(to_native(2,[]).replace('"qubits": 2','"qubits": 99'))
