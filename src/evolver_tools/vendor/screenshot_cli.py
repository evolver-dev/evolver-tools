#!/usr/bin/env python3
"""screenshot-cli — Take screenshots from terminal (requires import os; os.system)."""
import os, sys, time, subprocess, tempfile
from datetime import datetime

TOOL_META = {
    "name": "screenshot-cli",
    "desc": "Take screenshots from terminal (X11/Wayland/macOS/Windows)",
    "func": "main",
}

def _check_cmd(cmd):
    """Check if a command is available."""
    try:
        subprocess.run(["which", cmd], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def _screenshot_x11(output, delay, fullscreen):
    """X11 using import (ImageMagick) or scrot."""
    cmd = []
    if _check_cmd("import"):
        cmd = ["import"]
        if fullscreen:
            cmd.extend(["-window", "root"])
        if delay:
            cmd.extend(["-delay", str(delay)])
        cmd.append(output)
    elif _check_cmd("scrot"):
        cmd = ["scrot"]
        if delay:
            cmd.extend(["-d", str(delay)])
        cmd.append(output)
    else:
        return False
    subprocess.run(cmd)
    return True

def _screenshot_wayland(output, delay):
    """Wayland using grim or slurp."""
    if _check_cmd("grim"):
        area = []
        if _check_cmd("slurp"):
            r = subprocess.run(["slurp"], capture_output=True, text=True)
            if r.returncode == 0:
                area = ["-g", r.stdout.strip()]
        cmd = ["grim"] + area + [output]
        if delay:
            time.sleep(delay)
        subprocess.run(cmd)
        return True
    return False

def _screenshot_macos(output, delay):
    """macOS screencapture."""
    cmd = ["screencapture"]
    if delay:
        cmd.extend(["-T", str(delay)])
    cmd.append(output)
    subprocess.run(cmd)
    return True

def _screenshot_windows(output, delay):
    """Windows using PowerShell."""
    if delay:
        time.sleep(delay)
    ps = f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds | ForEach-Object {{ $b = $_; $bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height; $g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($b.X, $b.Y, 0, 0, $b.Size); $bmp.Save("{output}", [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $bmp.Dispose() }}'
    subprocess.run(["powershell", "-Command", ps])
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Take screenshots from terminal")
    parser.add_argument("-o", "--output", default="", help="Output path")
    parser.add_argument("-d", "--delay", type=int, default=0, help="Delay in seconds")
    parser.add_argument("-f", "--fullscreen", action="store_true", help="Fullscreen (X11)")
    parser.add_argument("--list", action="store_true", help="List available backends")
    args = parser.parse_args()

    if args.list:
        for name in ["import", "scrot", "grim", "screencapture", "powershell"]:
            print(f"  {name}: {'✓' if _check_cmd(name) else '✗'}")
        return

    output = args.output or os.path.join(tempfile.gettempdir(),
        f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")

    platform = sys.platform
    ok = False
    if platform == "darwin":
        ok = _screenshot_macos(output, args.delay)
    elif platform == "win32":
        ok = _screenshot_windows(output, args.delay)
    else:
        if os.environ.get("WAYLAND_DISPLAY"):
            ok = _screenshot_wayland(output, args.delay)
        if not ok:
            ok = _screenshot_x11(output, args.delay, args.fullscreen)

    if ok:
        print(f"Screenshot saved: {output}")
    else:
        print("No screenshot backend found. Install: import (ImageMagick), scrot, grim, or screencapture")
        sys.exit(1)

if __name__ == "__main__":
    main()
