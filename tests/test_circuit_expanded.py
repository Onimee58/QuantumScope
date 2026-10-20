import math
import numpy as np
from quantumscope.physics.circuits import Gate,zero,evolution,unitary,parse_qasm
from quantumscope.physics.circuit_files import to_native,from_native,to_qasm

def test_u_general_qasm_roundtrip():
    gates=[Gate('U',(0,),0.6,-0.3,1.2),Gate('P',(0,),0.7),Gate('SDG',(0,)),Gate('SX',(0,))]
    n,parsed=parse_qasm(to_qasm(1,gates))
    np.testing.assert_allclose(evolution(1,gates)[-1],evolution(n,parsed)[-1],atol=1e-12)
    nn,copy=from_native(to_native(n,parsed))
    np.testing.assert_allclose(evolution(nn,copy)[-1],evolution(n,parsed)[-1],atol=1e-12)

def test_u_is_unitary():
    for theta in [0,.4,math.pi]:
        U=unitary(Gate('U',(0,),theta,.9,1.4))
        np.testing.assert_allclose(U.conj().T@U,np.eye(2),atol=1e-12)

def test_toffoli_truth_table():
    for a in [0,1]:
        for b in [0,1]:
            for c in [0,1]:
                state=zero(3)
                init=[Gate('X',(i,)) for i,val in enumerate((a,b,c)) if val]
                result=evolution(3,init+[Gate('CCX',(0,1,2))])[-1]
                expected=(a<<2)|(b<<1)|(c^(a&b))
                assert np.argmax(abs(result))==expected

def test_cswap_truth_table():
    for ctrl in [0,1]:
        for a in [0,1]:
            for b in [0,1]:
                init=[Gate('X',(i,)) for i,val in enumerate((ctrl,a,b)) if val]
                state=evolution(3,init+[Gate('CSWAP',(0,1,2))])[-1]
                dest=(ctrl<<2)|((b if ctrl else a)<<1)|(a if ctrl else b)
                assert np.argmax(abs(state))==dest

def test_half_adder_example():
    for a in (0,1):
        for b in (0,1):
            initial=[Gate('X',(0,))] if a else []
            if b:initial.append(Gate('X',(1,)))
            ops=initial+[Gate('CCX',(0,1,2)),Gate('CX',(0,1))]
            index=np.argmax(abs(evolution(3,ops)[-1]))
            assert ((index>>1)&1)==(a^b)
            assert (index&1)==(a&b)

def test_half_subtractor_example():
    for a in (0,1):
        for b in (0,1):
            initial=[Gate('X',(0,))] if a else []
            if b:initial.append(Gate('X',(1,)))
            ops=initial+[Gate('X',(0,)),Gate('CCX',(0,1,2)),Gate('X',(0,)),Gate('CX',(0,1))]
            index=np.argmax(abs(evolution(3,ops)[-1]))
            assert ((index>>1)&1)==(a^b)
            assert (index&1)==((1-a)&b)

def test_qasm_rejects_bad_u():
    import pytest
    with pytest.raises(ValueError):parse_qasm('OPENQASM 2.0; qreg q[1]; u3(foo,0,0) q[0];')
