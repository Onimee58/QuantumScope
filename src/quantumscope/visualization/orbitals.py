"""VTK/PyVista visualization with probability-aware framing and GPU fallback."""
import numpy as np
import pyvista as pv
from quantumscope.visualization.phase import phase_with_node_mask
from quantumscope.physics.hydrogen import enclosing_density_threshold


def image_data(axis, scalar, name):
    step = float(axis[1] - axis[0])
    grid = pv.ImageData(dimensions=scalar.shape, spacing=(step,) * 3,
                        origin=(float(axis[0]),) * 3)
    grid.point_data[name] = np.asarray(scalar, dtype=np.float32).ravel(order="F")
    return grid


def probability_radius(axis, density, fraction=0.995):
    """Radius containing fraction of *sampled* probability, used only for camera framing."""
    step = float(axis[1] - axis[0])
    x, y, z = np.meshgrid(axis, axis, axis, indexing="ij", sparse=True)
    radii = np.sqrt(x*x + y*y + z*z).ravel()
    weights = density.ravel()
    order = np.argsort(radii)
    cumulative = np.cumsum(weights[order], dtype=np.float64)
    if cumulative.size == 0 or cumulative[-1] <= 0:
        return max(step, float(np.max(np.abs(axis))))
    index = np.searchsorted(cumulative, fraction * cumulative[-1])
    return float(max(3 * step, radii[order[min(index, len(order) - 1)]]))


def _frame(plotter, radius):
    """Keep physically meaningful coordinates while framing orbital, not entire grid."""
    distance = 3.1 * radius
    plotter.camera_position = [(distance, -distance, distance * 0.85),
                               (0, 0, 0), (0, 0, 1)]
    plotter.camera.SetClippingRange(0.01, 20 * distance)
    plotter.reset_camera_clipping_range()


def draw_orbital(plotter, axis, density, psi, mode, enclosed=90,
                 renderer="Auto (GPU preferred)", opacity_strength=1.0,
                 phase_coloring=False, show_grid=False, camera_view="Perspective", zoom=1.0):
    """Draw true spatial field; visual transfer function does not modify exported physics."""
    plotter.clear()
    plotter.set_background("#101820")
    backend = "Surface rendering"
    radius = probability_radius(axis, density)
    if mode == "Density cloud":
        peak = float(density.max())
        if peak <= 0:
            raise ValueError("Probability density is zero")
        # Perceptual enhancement only, not probability/density remapping in science arrays.
        display = np.power(np.clip(density / peak, 0.0, 1.0), 0.35)
        volume = image_data(axis, display, "display intensity")
        transfer = np.array([0, .003, .01, .025, .05, .09, .15, .25], dtype=float)
        transfer = np.clip(transfer * opacity_strength, 0, 1).tolist()
        mapper = ("fixed_point" if renderer == "CPU" else
                  "gpu" if renderer == "GPU" else "smart")
        args = dict(scalars="display intensity", cmap="viridis", opacity=transfer,
                    clim=(0, 1), shade=False, show_scalar_bar=False, mapper=mapper)
        try:
            plotter.add_volume(volume, **args)
            backend = {"gpu": "GPU volume mapper requested", "smart": "VTK smart mapper (GPU preferred)",
                       "fixed_point": "CPU volume mapper"}[mapper]
        except Exception:
            if renderer == "GPU":
                # Fail clearly for an explicitly selected GPU rather than silently change backend.
                raise
            plotter.add_volume(volume, **{**args, "mapper": "fixed_point"})
            backend = "CPU volume mapper (GPU unavailable)"
        # Explain intensity transformation rather than incorrectly label it density.
        plotter.add_text("Display intensity = (density / peak)^0.35", position="upper_left",
                         font_size=9, color="white")
    elif mode == "Probability enclosure":
        level = enclosing_density_threshold(density, float(axis[1]-axis[0]), enclosed/100)
        surface = image_data(axis, density, "density").contour(
            isosurfaces=[level], scalars="density")
        if surface.n_points:
            if phase_coloring:
                # Interpolate the *complex wavefunction* at surface vertices, not
                # nearest voxel cell centers. Nearest-cell phase coloring created
                # staircase/triangle artifacts around nodal features.
                from scipy.ndimage import map_coordinates
                verts = surface.points
                origin, step = float(axis[0]), float(axis[1] - axis[0])
                coords = ((verts - origin) / step).T
                real = map_coordinates(np.real(psi), coords, order=1, mode="nearest")
                imag = map_coordinates(np.imag(psi), coords, order=1, mode="nearest")
                surface.point_data["wavefunction phase (rad)"] = phase_with_node_mask(
                    real, imag, float(np.sqrt(np.max(density))))
                plotter.add_mesh(surface, scalars="wavefunction phase (rad)",
                                 preference="point", cmap="twilight", clim=(-np.pi, np.pi),
                                 opacity=0.96, smooth_shading=True, nan_color="gray",
                                 interpolate_before_map=False, show_scalar_bar=True,
                                 scalar_bar_args={"color": "white", "title": "phase (rad)", "vertical": True, "width": 0.055, "height": 0.48, "position_x": 0.92, "position_y": 0.27})
            else:
                plotter.add_mesh(surface, color="deepskyblue", opacity=0.78,
                                 smooth_shading=True, specular=0.32, specular_power=25,
                                 show_scalar_bar=False)
    else:
        field = np.real(psi) if mode == "Real(psi)" else np.imag(psi)
        magnitude = float(np.max(np.abs(field)))
        if magnitude > 1e-14:
            surface = image_data(axis, field, "amplitude").contour(
                isosurfaces=[-0.15*magnitude, 0.15*magnitude], scalars="amplitude")
            if surface.n_points:
                plotter.add_mesh(surface, scalars="amplitude", cmap="coolwarm",
                                 clim=(-magnitude, magnitude), opacity=0.72,
                                 smooth_shading=True, show_scalar_bar=True,
                                 scalar_bar_args={"color": "white", "title": "amplitude"})
        else:
            plotter.add_text("Imaginary component is zero for this state", position="upper_left",
                             font_size=11, color="white")
    plotter.add_axes()
    if show_grid:
        plotter.show_bounds(grid='back', location='outer', all_edges=False,
                            xtitle='x (a_mu)', ytitle='y (a_mu)', ztitle='z (a_mu)',
                            color='white', font_size=9)
    # nucleus is symbolic (not displayed to atomic physical scale)
    plotter.add_mesh(pv.Sphere(radius=max(radius * .012, .05), center=(0, 0, 0)),
                     color="orange", smooth_shading=True)
    _frame(plotter, radius)
    set_camera_view(plotter, radius, camera_view, zoom)
    plotter.render()
    return backend, radius


def set_camera_view(plotter, radius, camera_view="Perspective", zoom=1.0):
    """Stable orientation and magnification in unchanged Bohr-radius coordinates."""
    distance = max(1.0, 3.1 * radius) / max(0.5, min(float(zoom), 5.0))
    d = distance
    viewpoints = {
        "Perspective": ((d, -d, .85*d), (0, 0, 1)),
        "+X": ((d, 0, 0), (0, 0, 1)),
        "+Y": ((0, d, 0), (0, 0, 1)),
        "+Z": ((0, 0, d), (0, 1, 0)),
    }
    eye, up = viewpoints.get(camera_view, viewpoints["Perspective"])
    plotter.camera_position = [eye, (0, 0, 0), up]
    plotter.reset_camera_clipping_range()
