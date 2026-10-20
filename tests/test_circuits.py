import math
import numpy as np
import pytest
from quantumscope.physics.circuits import (Gate, apply_gate, bloch, evolution,
    parse_qasm, sample, zero, MAX_QUBITS)


def test_bell_pair_and_local_mixture():
    s=evolution(2,[Gate('H',(0,)),Gate('CX',(0,1))])[-1]
    np.testing.assert_allclose(s,[1/math.sqrt(2),0,0,1/math.sqrt(2)])
    np.testing.assert_allclose(bloch(s,2,0),(0,0,0),atol=1e-12)
    np.testing.assert_allclose(bloch(s,2,1),(0,0,0),atol=1e-12)


def test_bloch_pure_initial_and_hadamard():
    np.testing.assert_allclose(bloch(zero(1),1,0),(0,0,1))
    s=apply_gate(zero(1),1,Gate('H',(0,)))
    np.testing.assert_allclose(bloch(s,1,0),(1,0,0),atol=1e-12)


def test_x_y_z_rotation_and_swap():
    s=apply_gate(zero(2),2,Gate('X',(0,)))
    np.testing.assert_allclose(s,[0,0,1,0])
    s=apply_gate(s,2,Gate('SWAP',(0,1)))
    np.testing.assert_allclose(s,[0,1,0,0])
    r=apply_gate(zero(1),1,Gate('RY',(0,),math.pi))
    np.testing.assert_allclose(abs(r[1]),1,atol=1e-12)
    z=apply_gate(zero(2),2,Gate('CZ',(0,1)))
    np.testing.assert_allclose(z,[1,0,0,0])


def test_qasm_round_trip_subset():
    n,ops=parse_qasm('''OPENQASM 2.0;
    include "qelib1.inc"; qreg q[2];
    h q[0]; rx(pi/2) q[1]; cx q[0],q[1];''')
    assert n==2 and [g.name for g in ops]==['H','RX','CX']
    assert math.isclose(ops[1].angle,math.pi/2)


@pytest.mark.parametrize('source',[
    'OPENQASM 2.0; qreg q[2]; measure q[0] -> c[0];',
    'OPENQASM 2.0; qreg q[2]; foo q[0];',
    'OPENQASM 2.0; qreg q[2]; cx q[0],q[0];',
    'OPENQASM 2.0; qreg q[11];',
])
def test_qasm_unsupported_fails(source):
    with pytest.raises(ValueError):parse_qasm(source)


def test_sample_and_limit():
    counts=sample(zero(2),500,seed=3)
    assert counts.tolist()==[500,0,0,0]
    with pytest.raises(ValueError):zero(MAX_QUBITS+1)
