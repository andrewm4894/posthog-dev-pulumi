"""Remote Desktop: xrdp, XFCE, Chrome, and Chrome Remote Desktop."""

from config import RemoteDesktopConfig


def get_remote_desktop_install(remote_desktop: RemoteDesktopConfig) -> str:
    """Generate Remote Desktop package installation section (run before user creation)."""
    if not remote_desktop.enabled or not remote_desktop.password:
        return ""

    return '''
section_start "Remote Desktop Install"

echo "Installing XFCE desktop environment..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \\
    xfce4 xfce4-goodies \\
    dbus-x11 \\
    xorg

echo "Installing xrdp (RDP server)..."
apt-get install -y xrdp

# Add xrdp user to ssl-cert group (required for TLS)
usermod -aG ssl-cert xrdp

echo "Installing Chrome browser..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

echo "Installing Chrome Remote Desktop..."
wget -q https://dl.google.com/linux/direct/chrome-remote-desktop_current_amd64.deb -O /tmp/crd.deb
apt-get install -y /tmp/crd.deb || apt-get install -y -f
rm /tmp/crd.deb

# Enable and start xrdp (user config happens after user creation)
systemctl enable xrdp
systemctl start xrdp

section_end "Remote Desktop Install"
'''


def get_remote_desktop_config(remote_desktop: RemoteDesktopConfig) -> str:
    """Generate Remote Desktop user configuration section (run after user creation)."""
    if not remote_desktop.enabled or not remote_desktop.password:
        return ""

    return f'''
section_start "Remote Desktop Config"

# Add ph to chrome-remote-desktop group (if it exists)
if getent group chrome-remote-desktop > /dev/null 2>&1; then
    usermod -aG chrome-remote-desktop ph
    echo "Added ph to chrome-remote-desktop group"
else
    echo "Warning: chrome-remote-desktop group not found, creating it"
    groupadd chrome-remote-desktop
    usermod -aG chrome-remote-desktop ph
fi

# Configure Chrome Remote Desktop to use XFCE
echo "exec /usr/bin/xfce4-session" > /home/ph/.chrome-remote-desktop-session
chmod +x /home/ph/.chrome-remote-desktop-session
chown ph:ph /home/ph/.chrome-remote-desktop-session

# Configure XFCE as the session for xrdp
echo "xfce4-session" > /home/ph/.xsession
chown ph:ph /home/ph/.xsession

# Set password for ph user (for RDP login)
echo "ph:{remote_desktop.password}" | chpasswd

echo "Remote Desktop configured - connect via RDP to port 3389 (user: ph)"
section_end "Remote Desktop Config"
'''
