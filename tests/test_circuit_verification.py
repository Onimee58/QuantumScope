from quantumscope.physics.circuits import Gate
from quantumscope.physics.circuit_verification import inspect_basis,verify_example


def test_half_adder_exhaustive():
    gates=[Gate('X',(0,)),Gate('X',(1,)),Gate('CCX',(0,1,2)),Gate('CX',(0,1))]
    rows,_=verify_example('Half adder (a=1,b=1)',3,gates)
    assert len(rows)==4 and all(r.passed for r in rows)


def test_half_subtractor_exhaustive():
    gates=[Gate('X',(0,)),Gate('X',(1,)),Gate('X',(0,)),Gate('CCX',(0,1,2)),Gate('X',(0,)),Gate('CX',(0,1))]
    rows,_=verify_example('Half subtractor (a=1,b=1)',3,gates)
    assert len(rows)==4 and all(r.passed for r in rows)


def test_two_bit_adder_exhaustive():
    gates=[Gate('X',(1,)),Gate('X',(3,)),Gate('CCX',(1,3,4)),Gate('CX',(3,1)),Gate('CCX',(0,2,5)),Gate('CX',(0,2)),Gate('CCX',(2,4,5)),Gate('CX',(4,2))]
    rows,_=verify_example('2-bit ripple-carry adder (1+1)',6,gates)
    assert len(rows)==16 and all(r.passed for r in rows)


def test_general_quantum_inspection_not_binary_pass_fail():
    rows,_=inspect_basis(1,[Gate('H',(0,))])
    assert len(rows)==2
    assert all(r.passed is None and abs(r.probability-.5)<1e-9 for r in rows)
