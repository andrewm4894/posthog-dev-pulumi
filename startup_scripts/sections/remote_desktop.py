"""Remote Desktop: xrdp, XFCE, Chrome, and Chrome Remote Desktop."""

from config import RemoteDesktopConfig


def get_remote_desktop_install(remote_desktop: RemoteDesktopConfig) -> str:
    """Generate Remote Desktop package installation section (run before user creation)."""
    if not remote_desktop.enabled or not remote_desktop.password:
        return ""

    return '''
section_start "Remote Desktop Install"

echo "Installing XFCE desktop environment (minimal)..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \\
    xfce4 \\
    dbus-x11 \\
    xorg

echo "Installing Chrome browser..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

echo "Installing Chrome Remote Desktop..."
wget -q https://dl.google.com/linux/direct/chrome-remote-desktop_current_amd64.deb -O /tmp/crd.deb
apt-get install -y /tmp/crd.deb || apt-get install -y -f
rm /tmp/crd.deb

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

# Set password for ph user (needed for sudo in desktop session)
echo "ph:{remote_desktop.password}" | chpasswd

echo "Chrome Remote Desktop configured"
echo "To set up: SSH in, run the setup command from https://remotedesktop.google.com/headless"
section_end "Remote Desktop Config"
'''
