#!/usr/bin/env bash
set -euo pipefail
VERSION="${1:-0.6.1}"
ARCH=amd64
APP_DIR="dist/QuantumScope"
if [ ! -x "$APP_DIR/QuantumScope" ]; then echo "Missing $APP_DIR/QuantumScope. Run PyInstaller --onedir first." >&2; exit 1; fi
ROOT="build/deb-root"
rm -rf "$ROOT"
mkdir -p "$ROOT/DEBIAN" "$ROOT/opt/quantumscope" "$ROOT/usr/bin" "$ROOT/usr/share/applications" "$ROOT/usr/share/icons/hicolor/256x256/apps"
cp -a "$APP_DIR/." "$ROOT/opt/quantumscope/"
cp src/quantumscope/assets/quantumscope-256.png "$ROOT/usr/share/icons/hicolor/256x256/apps/quantumscope.png"
cat > "$ROOT/usr/bin/quantumscope" <<'EOF'
#!/bin/sh
exec /opt/quantumscope/QuantumScope "$@"
EOF
chmod 755 "$ROOT/usr/bin/quantumscope" "$ROOT/opt/quantumscope/QuantumScope"
cat > "$ROOT/usr/share/applications/quantumscope.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=QuantumScope
GenericName=Quantum Visualization Studio
Comment=Interactive quantum visualization experiments
Exec=/usr/bin/quantumscope
Icon=quantumscope
Terminal=false
Categories=Education;Science;Physics;
StartupNotify=true
EOF
cat > "$ROOT/DEBIAN/control" <<EOF
Package: quantumscope
Version: $VERSION
Section: science
Priority: optional
Architecture: $ARCH
Maintainer: QuantumScope contributors <https://github.com/Onimee58/QuantumScope>
Homepage: https://github.com/Onimee58/QuantumScope
Depends: libc6, libgl1, libegl1, libxkbcommon-x11-0
Description: QuantumScope quantum visualization studio
 Interactive visualization of hydrogen orbitals, quantum dynamics and double-slit interference.
EOF
chmod 644 "$ROOT/DEBIAN/control" "$ROOT/usr/share/applications/quantumscope.desktop"
mkdir -p dist/installers
dpkg-deb --build --root-owner-group "$ROOT" "dist/installers/quantumscope_${VERSION}_${ARCH}.deb"
echo "Created dist/installers/quantumscope_${VERSION}_${ARCH}.deb"
