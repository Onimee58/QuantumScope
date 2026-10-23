"""3D hydrogen-superposition scene, independent of the Qt widget.

Works with any PyVista plotter (the dialog's embedded QtInteractor, or an
off-screen Plotter in tests). Densities are exact; the volume transfer
function only changes appearance.
"""
import numpy as np
import pyvista as pv

VIEWS = {
    'isometric': 'view_isometric',
    'xy': 'view_xy',   # top: looking down the z axis
    'xz': 'view_xz',   # front: looking along the y axis
    'yz': 'view_yz',   # side: looking along the x axis
}


class HydrogenScene3D:
    def __init__(self, plotter):
        self.plotter = plotter
        self.model = None
        self._grid = None
        self._actor = None
        self._actor_key = None      # (mode, visibility) the current actor was built for
        self._axes_added = False
        self._view_set = False      # the camera is placed once; later changes keep the user's view

    # ---- data ------------------------------------------------------------------------
    def set_model(self, model, n, extent):
        """Sample both eigenstates once on an n³ grid of half-width `extent`."""
        self.model = model
        axis = np.linspace(-extent, extent, n)
        x, y, z = np.meshgrid(axis, axis, axis, indexing='ij', sparse=True)
        psi_a = np.asarray(model.first.wavefunction(x, y, z), dtype=np.complex64)
        psi_b = np.asarray(model.second.wavefunction(x, y, z), dtype=np.complex64)
        shape = (n, n, n)
        self._aa = np.broadcast_to(np.abs(psi_a) ** 2, shape).astype(np.float32).copy()
        self._bb = np.broadcast_to(np.abs(psi_b) ** 2, shape).astype(np.float32).copy()
        self._cross = np.broadcast_to(np.conjugate(psi_a) * psi_b, shape).astype(np.complex64).copy()
        self._peak = max(float(max(np.max(self._aa), np.max(self._bb)) * 2.5), 1e-12)
        self._grid = pv.ImageData(dimensions=shape, spacing=(axis[1] - axis[0],) * 3, origin=(axis[0],) * 3)
        self._grid.point_data['density'] = np.zeros(n ** 3, dtype=np.float32)
        self._grid.point_data['intensity'] = np.zeros(n ** 3, dtype=np.float32)
        self._remove_actor()

    def clear(self):
        self.model = None
        self._grid = None
        self._remove_actor()
        self.plotter.render()

    def frame_density(self, fraction):
        """Exact density at `fraction` of a beat period (stationary if degenerate)."""
        p = self.model.probability_first
        theta = (self.model.relative_phase - 2 * np.pi * fraction
                 if np.isfinite(self.model.beat_period_fs) else self.model.relative_phase)
        return (p * self._aa + (1 - p) * self._bb
                + 2 * np.sqrt(p * (1 - p)) * np.real(np.exp(1j * theta) * self._cross)).clip(0).astype(np.float32)

    # ---- drawing ----------------------------------------------------------------------
    def draw(self, fraction, mode='volume', visibility=1.4):
        """Draw the frame. Playback updates the existing actor in place."""
        if self.model is None or self._grid is None:
            return
        density = self.frame_density(fraction)
        if mode == 'volume':
            intensity = (density / self._peak) ** (0.60 / visibility)
            key = ('volume', round(visibility, 6))
            if self._actor is not None and self._actor_key == key:
                data = self._actor.mapper.dataset
                data.point_data['intensity'][:] = intensity.ravel(order='F')
                data.Modified()
            else:
                self._remove_actor()
                self._grid.point_data['intensity'] = intensity.astype(np.float32).ravel(order='F')
                self._actor = self.plotter.add_volume(self._grid, scalars='intensity', cmap='viridis', clim=(0, 1),
                                                      opacity='sigmoid', mapper='smart', show_scalar_bar=False,
                                                      reset_camera=False)
                self._actor_key = key
        else:
            # The surface's shape changes with time, so it is recomputed each frame.
            self._grid.point_data['density'] = density.ravel(order='F')
            positive = density[density > 0]
            cutoff = float(np.quantile(positive, .75)) if positive.size else 1e-12
            mesh = self._grid.contour([cutoff], scalars='density')
            self._remove_actor()
            if mesh.n_points:
                self._actor = self.plotter.add_mesh(mesh, color='#4eb5d6', smooth_shading=True,
                                                    opacity=min(.95, .50 + .12 * visibility), reset_camera=False)
                self._actor_key = ('surface', round(visibility, 6))
        if not self._axes_added:
            self.plotter.add_axes()
            self._axes_added = True
        if not self._view_set:
            self.reset_view('isometric', render=False)
        self.plotter.render()

    def _remove_actor(self):
        if self._actor is not None:
            self.plotter.remove_actor(self._actor, render=False)
        self._actor = None
        self._actor_key = None

    # ---- camera ------------------------------------------------------------------------
    def reset_view(self, view='isometric', render=True):
        """Standard viewing direction, centered and zoomed to fit the data."""
        getattr(self.plotter, VIEWS[view])(render=False)
        self.plotter.reset_camera(render=False)
        self._view_set = True
        if render:
            self.plotter.render()
