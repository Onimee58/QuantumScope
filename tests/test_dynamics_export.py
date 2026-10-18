import numpy as np
from quantumscope.physics.dynamics_export import density_frames

def test_gif_frames_periodic_sampling():
    a=np.array([1.,1.]); b=np.array([1.,-1.]); count=72
    values=list(density_frames(a,b,.5,0,count))
    assert len(values)==count
    assert np.allclose(values[0], np.array([2.,0.]))
    assert not np.allclose(values[0],values[1])
    assert np.allclose(values[18],np.array([1.,1.]))

def test_gif_frames_preserve_probability_for_orthogonal_vectors():
    a=np.array([1.,0.]); b=np.array([0.,1.])
    assert all(np.isclose(v.sum(),1) for v in density_frames(a,b,.4,.7,24))
