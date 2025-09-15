%define name iotplatform-gateway
%define version 3.7.7
%define release 1

Summary: IOTPlatform Gateway for IoT devices.
Name: %{name}
Version: %{version}
Release: %{release}
License: Apache License, Version 2.0
Group: Applications/System
BuildArch: noarch
Vendor: IOTPlatform <info@seariot.io>
Url: https://github.com/seariiot/iotplatform-gateway

# Sources:
Source0: iotplatform-gateway.service
Source1: configs.tar.gz
Source2: iotplatform_gateway-%{version}-py3-none-any.whl
Source3: extensions.tar.gz

%description
The IOTPlatform IoT Gateway integrates devices using different protocolos like MQTT, Modbus, OPC-UA and other.

%install

# Install the systemd service file.
mkdir -p %{buildroot}/etc/systemd/system
install -m 644 %{SOURCE0} %{buildroot}/etc/systemd/system/iotplatform-gateway.service

# Install the configuration tarball.
mkdir -p %{buildroot}/etc/iotplatform-gateway
mkdir -p %{buildroot}/etc/iotplatform-gateway/config
tar -xzf %{SOURCE1} -C %{buildroot}/etc/iotplatform-gateway

# Install the wheel file into /var/lib/iotplatform_gateway.
mkdir -p %{buildroot}/var/lib/iotplatform_gateway
install -m 644 %{SOURCE2} %{buildroot}/var/lib/iotplatform_gateway/

# Install extensions into /var/lib/iotplatform_gateway.
install -m 755 %{SOURCE3} %{buildroot}/var/lib/iotplatform_gateway/

# Create logs directory.
mkdir -p %{buildroot}/var/log/iotplatform-gateway

# (Ownership is set later via %defattr.)

%pre
getent passwd iotplatform_gateway || useradd -r -U -d /var/lib/iotplatform_gateway -c "IOTPlatform-Gateway Service" iotplatform_gateway

%post
# Create the Python virtual environment if not present.
if [ ! -d /var/lib/iotplatform_gateway/venv ]; then
    python3 -m venv /var/lib/iotplatform_gateway/venv
    /var/lib/iotplatform_gateway/venv/bin/pip install --upgrade pip setuptools
fi
# Install the locally built wheel into the venv.
if [ -f /var/lib/iotplatform_gateway/iotplatform_gateway-%{version}-py3-none-any.whl ]; then
    /var/lib/iotplatform_gateway/venv/bin/pip install --upgrade --force-reinstall /var/lib/iotplatform_gateway/iotplatform_gateway-%{version}-py3-none-any.whl
else
    echo "Error: Wheel file not found in /var/lib/iotplatform_gateway" >&2
    exit 1
fi

# Extract extensions tarball into /var/lib/iotplatform_gateway
if [ -f /var/lib/iotplatform_gateway/extensions.tar.gz ]; then
    if [ ! -d /var/lib/iotplatform_gateway/extensions ]; then
        echo "Extracting extensions from extensions.tar.gz..."
        mkdir -p /var/lib/iotplatform_gateway/extensions
        tar -xzf /var/lib/iotplatform_gateway/extensions.tar.gz -C /var/lib/iotplatform_gateway/extensions
        rm -f /var/lib/iotplatform_gateway/extensions.tar.gz
    else
        echo "Directory /var/lib/iotplatform_gateway/extensions exists. Creating backup as extensions_backup.tar.gz..."
        tar -czf /var/lib/iotplatform_gateway/extensions_backup.tar.gz -C /var/lib/iotplatform_gateway extensions
    fi
fi

# Extract the configuration tarball into /etc/iotplatform-gateway.
if [ -f /etc/iotplatform-gateway/configs.tar.gz ]; then
    if [ ! -d /etc/iotplatform-gateway/config ]; then
        echo "Extracting configuration files from configs.tar.gz..."
        tar -xzf /etc/iotplatform-gateway/configs.tar.gz -C /etc/iotplatform-gateway
    else
        echo "Directory /etc/iotplatform-gateway/config exists. Creating backup as configs_backup.tar.gz..."
        tar -czf /etc/iotplatform-gateway/configs_backup.tar.gz -C /etc/iotplatform-gateway config
    fi
fi

echo "Setting ownership for directories..."
chown -R iotplatform_gateway:iotplatform_gateway /var/lib/iotplatform_gateway
chown -R iotplatform_gateway:iotplatform_gateway /etc/iotplatform-gateway
chown -R iotplatform_gateway:iotplatform_gateway /var/log/iotplatform-gateway

systemctl enable iotplatform-gateway.service
systemctl start iotplatform-gateway.service

%clean
rm -rf %{buildroot}

%files
%attr(0644,iotplatform_gateway,iotplatform_gateway) /etc/systemd/system/iotplatform-gateway.service
%dir %attr(0755,iotplatform_gateway,iotplatform_gateway) /etc/iotplatform-gateway
%config(noreplace) %attr(0644,iotplatform_gateway,iotplatform_gateway) /etc/iotplatform-gateway/config/*
%attr(0755,iotplatform_gateway,iotplatform_gateway) /var/lib/iotplatform_gateway
%attr(0755,iotplatform_gateway,iotplatform_gateway) /var/log/iotplatform-gateway

%postun
if [ "$1" = 0 ]; then
    echo "Cleaning up..."
    systemctl stop iotplatform-gateway
    userdel iotplatform_gateway
    rm -rf /var/lib/iotplatform_gateway
    rm -rf /var/log/iotplatform-gateway
    rm -rf /etc/iotplatform-gateway
fi
