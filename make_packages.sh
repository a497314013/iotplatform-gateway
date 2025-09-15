#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

# --- Automatically install required system packages ---
REQUIRED_PKGS=("rpm" "zstd" "xz-utils")
for pkg in "${REQUIRED_PKGS[@]}"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
         echo "Package '$pkg' is not installed. Checking availability..."
         if apt-cache show "$pkg" >/dev/null 2>&1; then
             echo "Installing $pkg..."
             sudo apt-get update && sudo apt-get install -y "$pkg"
         else
             echo "Error: Package '$pkg' not found. Please ensure your repositories are enabled and try again."
             exit 1
         fi
    fi
done

# Extract the current version from iotplatform_gateway/version.py
CURRENT_VERSION=$(grep -Po 'VERSION[ ,]=[ ,]"\K(([0-9])+(\.){0,1})+' iotplatform_gateway/version.py)

# --- Clean Block ---
if [ "${1:-}" = "clean" ] || [ "${1:-}" = "only_clean" ]; then
    for d in "/var/log/iotplatform-gateway/" "/var/lib/iotplatform_gateway/" "/etc/iotplatform-gateway/"; do
      if [ -d "$d" ]; then
          sudo rm -rf "$d"
          echo "Directory $d - removed."
      else
          echo "$d does not exist, skipping..."
      fi
    done

    for d in "deb_dist/" "dist/" "iotplatform-gateway.egg-info" "build/"; do
      if [ -d "$d" ]; then
          sudo rm -rf "$d"
          echo "Directory $d - removed."
      else
          echo "$d does not exist, skipping..."
      fi
    done

    for f in "iotplatform-gateway-${CURRENT_VERSION}.tar.gz" "configs.tar.gz" "iotplatform_gateway.tar.gz"; do
      if [ -f "$f" ]; then
          sudo rm -rf "$f"
          echo "File $f - removed."
      else
          echo "$f file does not exist, skipping..."
      fi
    done

    for f in "iotplatform-gateway-*.deb" "python3-iotplatform-gateway.deb" "python3-iotplatform-gateway.rpm" "iotplatform-gateway-*.noarch.rpm"; do
      if ls $f 1> /dev/null 2>&1; then
          sudo rm -rf $f
          echo "File $f - removed."
      else
          echo "No files matching $f found, skipping..."
      fi
    done

    if compgen -G "iotplatform_gateway-*.whl" > /dev/null; then
        sudo rm -f iotplatform_gateway-*.whl
        echo "File $f - removed."
    else
        echo "No iotplatform_gateway-*.whl files found, skipping..."
    fi

    sudo rm -rf iotplatform_gateway/config/backup || echo "Backup folder not found, skipping..."
    sudo rm -rf docker/config docker/extensions || echo "Docker directories not found, skipping..."
    sudo rm -rf for_build/etc/iotplatform-gateway/*
    sudo rm -rf for_build/var/lib/iotplatform_gateway/*
    sudo find iotplatform_gateway/ -name "*.pyc" -exec rm -f {} \;
    sudo apt remove python3-iotplatform-gateway -y || echo "Package not installed, skipping..."

    echo "All generated files removed."
fi

sudo rm -rf iotplatform_gateway/logs/*

if [[ "${2:-}" == "offline-build" ]]; then
  sudo mkdir -p /var/lib/iotplatform_gateway
  sudo cp -r requirements-full.txt /var/lib/iotplatform_gateway/
  sudo chown -R "$USER":"$USER" /var/lib/iotplatform_gateway

  python3.11 -m venv /var/lib/iotplatform_gateway/venv
  source /var/lib/iotplatform_gateway/venv/bin/activate
  pip install -r requirements-full.txt
  sudo cp /var/lib/iotplatform_gateway/venv iotplatform_gateway -r

  echo "Building offline package with full requirements..."
  tar -czf venv.tar.gz -C iotplatform_gateway venv
  ls
  pwd
fi

if [ "${1:-}" != "only_clean" ]; then

  CURRENT_USER=$USER
  export PYTHONDONTWRITEBYTECODE=1

  echo "Building DEB package"

  # --- Ensure pip and build module are installed ---
  if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "pip not found. Bootstrapping pip with ensurepip..."
    python3 -m ensurepip --upgrade || { echo "Error: pip bootstrapping failed."; exit 1; }
    python3 -m pip install --upgrade --break-system-packages pip
  fi
  python3 -m pip install --upgrade --break-system-packages build

  python3 -m build --no-isolation --wheel --outdir .
  WHEEL_FILE=$(ls | grep -E 'iotplatform_gateway-.*\.whl' | head -n 1)
  echo "Found wheel: $WHEEL_FILE"
  if [ ! -f "$WHEEL_FILE" ]; then
    echo "Error: Wheel file $WHEEL_FILE not found."
    exit 1
  fi

  # Create configs.tar.gz from the iotplatform_gateway/config folder if not present.
if [ ! -f configs.tar.gz ]; then
    echo "Creating configs.tar.gz from the iotplatform_gateway/config folder..."
    TEMP_CONFIG_DIR=$(mktemp -d)
    cp -r iotplatform_gateway/config "$TEMP_CONFIG_DIR/"
    sed -i 's#\./logs/#/var/log/iotplatform-gateway/#g' "$TEMP_CONFIG_DIR/config/logs.json"
    tar -czf configs.tar.gz -C "$TEMP_CONFIG_DIR" config
    rm -rf "$TEMP_CONFIG_DIR"
fi


  # Create extensions.tar.gz from the iotplatform_gateway/extensions folder if not present.
  if [ ! -f extensions.tar.gz ]; then
      echo "Creating extensions.tar.gz from the iotplatform_gateway/extensions folder..."
      tar -czf extensions.tar.gz -C iotplatform_gateway extensions
      ls
      pwd
  fi

  # --- Prepare DEB packaging ---
  if [ -d deb_dist ]; then
    sudo chown -R "$USER":"$USER" deb_dist
  fi
  mkdir -p deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway
  mkdir -p for_build/var/lib
  mkdir -p deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway/DEBIAN

  cat <<EOT > deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway/DEBIAN/control
Package: python3-iotplatform-gateway
Version: $CURRENT_VERSION
Section: python
Priority: optional
Architecture: all
Essential: no
Installed-Size: $(du -ks for_build/var/lib | cut -f1)
Maintainer: IOTPlatform <info@seariiot.io>
Description: IOTPlatform IoT Gateway
 The IOTPlatform Gateway service for handling MQTT, Modbus, OPC-UA, and other connectors.
Depends: python3, python3-venv
EOT

  mkdir -p for_build/var/lib/iotplatform_gateway
  cp extensions.tar.gz for_build/var/lib/iotplatform_gateway
  mkdir -p for_build/etc/iotplatform-gateway
  cp configs.tar.gz for_build/etc/iotplatform-gateway

  if [[ "${2:-}" == "offline-build" ]]; then
    cp venv.tar.gz for_build/var/lib/iotplatform_gateway
  fi

  rm -f for_build/var/lib/iotplatform_gateway/iotplatform_gateway-*.whl
  cp -r "$WHEEL_FILE" for_build/var/lib/iotplatform_gateway/"$WHEEL_FILE"
  cp -r for_build/etc deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway
  cp -r for_build/var deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway
  cp -r -a for_build/DEBIAN deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway

  sudo chown -R root:root deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway/
  sudo chown -R root:root deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway/var/
  sudo chmod 775 deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway/DEBIAN/preinst
  sudo chmod +x deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway/DEBIAN/postinst
  sudo chown root:root deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway/DEBIAN/preinst

  dpkg-deb -b deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway/

  mkdir deb-temp
  cd deb-temp
  ar x ../deb_dist/iotplatform-gateway-"$CURRENT_VERSION"/debian/python3-iotplatform-gateway.deb
  zstd -d *.zst || echo "No .zst files found or decompression failed."
  rm -f *.zst
  xz *.tar || echo "No .tar.xz files found or decompression failed."
  ar r ../python3-iotplatform-gateway.deb debian-binary control.tar.xz data.tar.xz
  cd ..
  rm -r deb-temp

  echo "DEB package built successfully."

  ####################################
  # Build RPM Package using rpmbuild
  ####################################
  echo "Building RPM package"

  if ! command -v rpmbuild >/dev/null 2>&1; then
    echo "rpmbuild command not found. Installing rpm package..."
    sudo apt-get update && sudo apt-get install -y rpm
    if ! command -v rpmbuild >/dev/null 2>&1; then
         echo "Error: rpmbuild still not found after installing rpm. Exiting."
         exit 1
    fi
  fi

  # Ensure the rpmbuild directory tree exists.
  for sub in BUILD RPMS SOURCES SPECS SRPMS; do
      mkdir -p ~/rpmbuild/$sub
  done

  # Copy sources to rpmbuild/SOURCES.
  cp for_build/etc/systemd/system/iotplatform-gateway.service ~/rpmbuild/SOURCES/
  cp configs.tar.gz ~/rpmbuild/SOURCES/
  cp extensions.tar.gz ~/rpmbuild/SOURCES/
  cp "$WHEEL_FILE" ~/rpmbuild/SOURCES/

  if [[ "${2:-}" == "offline-build" ]]; then
    echo "Copy venv to rpm"
    cp venv.tar.gz ~/rpmbuild/SOURCES/
  fi

  # Copy the spec file to rpmbuild/SPECS.
  if [[ "${2:-}" == "offline-build" ]]; then
    cp iotplatform-gateway-offline.spec ~/rpmbuild/SPECS/
  else
    cp iotplatform-gateway.spec ~/rpmbuild/SPECS/
  fi

  # Build the RPM.
  if [[ "${2:-}" == "offline-build" ]]; then
    rpmbuild -ba ~/rpmbuild/SPECS/iotplatform-gateway-offline.spec
  else
    rpmbuild -ba ~/rpmbuild/SPECS/iotplatform-gateway.spec
  fi

  if ls ~/rpmbuild/RPMS/noarch/*.rpm 1> /dev/null 2>&1; then
      cp ~/rpmbuild/RPMS/noarch/*.rpm .
      mv iotplatform-gateway-"$CURRENT_VERSION"-1.noarch.rpm python3-iotplatform-gateway.rpm
      chown "$CURRENT_USER":"$CURRENT_USER" python3-iotplatform-gateway.rpm
      echo "RPM package built successfully."
  else
      echo "RPM build did not produce any RPM files."
  fi

fi
