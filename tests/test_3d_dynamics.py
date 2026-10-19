import numpy as np
from quantumscope.physics.hydrogen import HydrogenAtom
from quantumscope.physics.dynamics import HydrogenSuperposition


def test_3d_interference_density_agrees_with_solver():
    atom=HydrogenAtom()
    model=HydrogenSuperposition(atom.state(1,0,0),atom.state(2,1,0),0.5,0.3)
    axis=np.linspace(-10,10,20)
    xyz=np.meshgrid(axis,axis,axis,indexing='ij',sparse=True)
    a=model.first.wavefunction(*xyz)
    b=model.second.wavefunction(*xyz)
    theta=model.relative_phase-2*np.pi*0.25
    predicted=0.5*np.abs(a)**2+0.5*np.abs(b)**2+np.real(np.conjugate(a)*b*np.exp(1j*theta))
    actual=model.density(*xyz,time_fs=model.beat_period_fs*0.25)
    np.testing.assert_allclose(predicted,actual,atol=1e-13,rtol=1e-10)
