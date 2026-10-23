# QuantumScope v0.2.0 — Visual workspace candidate

QuantumScope now uses a modern dark, single-window tabbed workspace. Select an experiment using the header shortcuts or Experiments menu. The persistent Hydrogen Explorer, Hydrogen Dynamics 2D, Hydrogen Dynamics 3D, and Double-Slit Experiment coexist in one main window. Existing experiment controls, plots, animation models, and export features are preserved.

The double-slit apparatus is an illustrative schematic, not a path reconstruction or full wave-propagation calculation. Experiment physics is the documented Fraunhofer far-field model.

**Release status:** source build candidate; physics tests pass but Qt/VTK GUI behavior must be verified on Linux and Windows before publishing a stable binary release.

# QuantumScope v0.2.0 — Quantum Phenomena Lab (First Stable Release)

QuantumScope now combines the hydrogen orbital explorer, 2D/3D hydrogen dynamics, and a new double-slit experiment in a single cross-platform application.

## New in v0.2.0

- **Animated apparatus:** source, double-slit barrier, expanding illustrative phase fronts, and detector with points marking simulated hits. Animation can be disabled; visual spacing is not to scale.
- **Double-Slit Experiment:** normalized coherent Fraunhofer far-field intensity distribution, with controls for wavelength, slit width, slit separation, screen distance and viewing range.
- **Simulated detections:** accumulate individual random screen hits sampled from the theoretical probability density; compare the histogram to the model.
- **CSV exports:** export theoretical distribution and simulated detections.
- **Versioned release artifacts:** tagged builds use the tag in the filenames; manual builds are labeled `dev`.
- **Preserved:** hydrogen orbital explorer, orbital comparison, NVIDIA launch support on Linux, hydrogen 2D and 3D dynamics, and GIF exports.

## Scientific limitations

The double-slit experiment uses an idealized coherent, monochromatic, equal-slit, paraxial Fraunhofer approximation. The phase-front animation is an explanatory schematic, not a model of particle trajectories or physical propagation times. It is *not* a time-dependent wave propagation simulation or real measured detector data. Hydrogen remains a nonrelativistic isolated-atom model.

## Platforms

Windows and Linux, with standalone ZIP applications built by GitHub Actions. Physics tests run automatically. Test packaged executables on both operating systems before marking this GitHub release Stable.

## Developer

Md. Saif Hassan Onim, PhD — https://people.smu.edu/monim

MIT License — https://github.com/Onimee58/QuantumScope
