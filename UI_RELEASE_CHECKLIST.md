# QuantumScope v0.2.0 — final desktop UI checklist

This source ZIP contains the updated Qt desktop GUI plus the existing native installer GitHub Actions workflow. It does **not** contain compiled installers.

1. Launch QuantumScope on Ubuntu. Verify the official Q/Wave image is shown in the header and Hydrogen Explorer tab. Window-frame icon display varies by window manager (GNOME/Wayland may not show it in the title bar).
2. Click **+ New Experiment** in the header and **+** at the right edge of the tabs. Confirm both menus open Hydrogen Dynamics 2D, Hydrogen Dynamics 3D, and Double-Slit Experiment within the main window.
3. Switch among tabs, close/reopen experiments, and check simulations and CSV exports.
4. Open **Settings** and change the theme; restart the app to confirm the preference persists. Default is dark. Some scientific renderers keep their own plotting palette regardless of interface theme.
5. Check **About** and GitHub link.
6. Push to the repository and run **Build installable QuantumScope releases** in GitHub Actions. Validate the resulting `.deb` on Ubuntu and setup `.exe` on Windows before tagging v0.2.0.

Automated check performed on the source: 40 physics tests passed (`PYTHONPATH=src python -m pytest -q`); all Python sources compile. Native desktop GUI and installer end-to-end behavior must be tested on their target systems.
