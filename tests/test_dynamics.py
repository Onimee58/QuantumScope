import numpy as np
import pytest
from scipy import constants
from quantumscope.physics.hydrogen import HydrogenAtom
from quantumscope.physics.dynamics import HydrogenSuperposition

A=HydrogenAtom()

def test_invalid_same_state():
    with pytest.raises(ValueError): HydrogenSuperposition(A.state(1,0,0),A.state(1,0,0))

def test_invalid_coefficients():
    with pytest.raises(ValueError): HydrogenSuperposition(A.state(1,0,0),A.state(2,1,0),1.2)

def test_stationary_if_single_state():
    m=HydrogenSuperposition(A.state(1,0,0),A.state(2,1,0),1.)
    x=np.array([0.,1.]); y=z=np.array([0.,0.])
    assert np.allclose(m.density(x,y,z,0),m.density(x,y,z,15))

def test_periodic_density():
    m=HydrogenSuperposition(A.state(1,0,0),A.state(2,1,0))
    x=np.array([0.,0.5,1.]); y=np.array([0.,0.,0.]); z=np.array([1.,2.,3.])
    assert np.allclose(m.density(x,y,z,0),m.density(x,y,z,m.beat_period_fs),rtol=1e-10,atol=1e-12)

def test_beat_period():
    m=HydrogenSuperposition(A.state(1,0,0),A.state(2,1,0))
    expected=2*np.pi*constants.hbar/(abs(m.energies_ev[1]-m.energies_ev[0])*constants.e)*1e15
    assert m.beat_period_fs==pytest.approx(expected)

def test_degenerate_stationary_density():
    m=HydrogenSuperposition(A.state(2,0,0),A.state(2,1,0))
    assert np.isinf(m.beat_period_fs)
    x=np.array([1.,2.]); y=np.zeros(2); z=np.array([1.,2.])
    assert np.allclose(m.density(x,y,z,0),m.density(x,y,z,10))

def test_grid_slice():
    m=HydrogenSuperposition(A.state(1,0,0),A.state(2,1,0))
    axis, d=m.slice_density(resolution=64,plane='xz')
    assert len(axis)==64 and d.shape==(64,64) and np.all(d>=0)

def test_spatial_probability_constant():
    m=HydrogenSuperposition(A.state(1,0,0),A.state(2,1,0),.37)
    axis=np.linspace(-25,25,66)
    x,y,z=np.meshgrid(axis,axis,axis,indexing='ij',sparse=True)
    probs=[np.sum(m.density(x,y,z,t))*(axis[1]-axis[0])**3 for t in (0,m.beat_period_fs*.29,m.beat_period_fs*.73)]
    assert max(probs)-min(probs)<.006
    assert all(abs(q-1)<.03 for q in probs)
