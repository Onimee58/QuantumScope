import math
import pytest
from quantumscope.physics.gate_education import parse_angle, gate_information, transformation_rows
from quantumscope.physics.circuits import ALL

@pytest.mark.parametrize('formula,expected', [('pi/2',math.pi/2),('-π/4',-math.pi/4),('2*pi',2*math.pi),('(pi+pi)/2',math.pi),('pi^2',math.pi**2)])
def test_angle_expressions(formula,expected):
    assert parse_angle(formula)==pytest.approx(expected)

@pytest.mark.parametrize('invalid',['__import__("os")','pi.__class__','1/0','2**1000','nan','sin(pi)',''])
def test_angle_rejects_unsafe(invalid):
    with pytest.raises(ValueError):parse_angle(invalid)

def test_reference_coverage():
    for gate in (*ALL,'M'):
        assert gate_information(gate)['name']==gate
        assert transformation_rows(gate)

def test_hadamard_mapping():
    rows=transformation_rows('H')
    assert len(rows)==2
    assert '|0>' in rows[0][1] and '|1>' in rows[0][1]
