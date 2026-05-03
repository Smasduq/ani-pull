#!/bin/bash

# Exit on error
set -e

VERSION="1.1.0"
DEB_FILE="../ani-pull_${VERSION}-1_all.deb"
DISTS=("bookworm" "bullseye" "trixie" "jammy" "noble")

echo "--- Starting Release Process for v$VERSION ---"

# 1. Build Debian Package
echo "[1/3] Building Debian package..."
dpkg-buildpackage -us -uc -b

# 2. Add to Reprepro
echo "[2/3] Adding to Reprepro repository..."
for dist in "${DISTS[@]}"; do
    echo "  Adding to $dist..."
    reprepro -b repo/ includedeb "$dist" "$DEB_FILE"
done

# 3. Export Repository
echo "[3/3] Exporting repository metadata..."
reprepro -b repo/ export

echo ""
echo "--- Build Complete! ---"
echo "Debian Repo updated in repo/"
echo ""
echo "Next Steps for other distros:"
echo "Fedora: rpmbuild -ba packaging/fedora/ani-pull.spec"
echo "Arch:   cd packaging/arch && makepkg -si"
