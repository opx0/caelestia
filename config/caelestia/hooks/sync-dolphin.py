#!/usr/bin/env python3
"""
Sync Caelestia color scheme with KDE kdeglobals for Dolphin and Qt applications.
Ensures authentic, vibrant Catppuccin Mocha colors rather than dull/washed-out M3 tones.
"""

import configparser
import json
import os
import subprocess
from pathlib import Path

CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
DATA_DIR = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share"))
STATE_DIR = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local/state"))

CAELESTIA_COLORS = CONFIG_DIR / "qtengine" / "caelestia.colors"
KDEGLOBALS = CONFIG_DIR / "kdeglobals"
COLOR_SCHEMES_DIR = DATA_DIR / "color-schemes"
CAELESTIA_KDE_SCHEME = COLOR_SCHEMES_DIR / "Caelestia.colors"
CATPPUCCIN_MOCHA_SCHEME = COLOR_SCHEMES_DIR / "CatppuccinMochaLavender.colors"
SCHEME_JSON = STATE_DIR / "caelestia" / "scheme.json"

def hex_to_rgb(hex_str: str) -> str:
    hex_clean = hex_str.strip().lstrip("#")
    if len(hex_clean) == 6:
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        return f"{r},{g},{b}"
    return hex_str.strip()

def rgb_to_hex(val: str) -> str:
    parts = [p.strip() for p in val.split(',')]
    if len(parts) == 3:
        try:
            r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return val
    return val

def sync():
    # Detect if active scheme is Catppuccin
    is_catppuccin = True
    if SCHEME_JSON.exists():
        try:
            s_data = json.loads(SCHEME_JSON.read_text())
            if s_data.get("name") != "catppuccin":
                is_catppuccin = False
        except Exception:
            pass

    # Source palette selection:
    # If Catppuccin is active and official scheme exists, use authentic Catppuccin Mocha colors!
    parser_src = configparser.ConfigParser(interpolation=None)
    parser_src.optionxform = str

    using_official_catppuccin = False
    if is_catppuccin and CATPPUCCIN_MOCHA_SCHEME.exists():
        parser_src.read(CATPPUCCIN_MOCHA_SCHEME)
        using_official_catppuccin = True
    elif CAELESTIA_COLORS.exists():
        parser_src.read(CAELESTIA_COLORS)
    else:
        print("[sync-dolphin] No color source available.")
        return

    # Read existing kdeglobals
    parser_dst = configparser.ConfigParser(interpolation=None)
    parser_dst.optionxform = str
    if KDEGLOBALS.exists():
        parser_dst.read(KDEGLOBALS)

    # Color sections to copy
    color_sections = [
        "Colors:Button",
        "Colors:Complementary",
        "Colors:Header",
        "Colors:Header][Inactive",
        "Colors:Selection",
        "Colors:Tooltip",
        "Colors:View",
        "Colors:Window",
        "ColorEffects:Disabled",
        "ColorEffects:Inactive",
        "WM"
    ]

    for section in color_sections:
        if parser_src.has_section(section):
            if not parser_dst.has_section(section):
                parser_dst.add_section(section)
            for k, v in parser_src.items(section):
                if v.startswith("#"):
                    v = hex_to_rgb(v)
                parser_dst.set(section, k, v)

    # Metadata
    if not parser_dst.has_section("General"):
        parser_dst.add_section("General")
    scheme_name = "CatppuccinMochaLavender" if using_official_catppuccin else "Caelestia"
    parser_dst.set("General", "ColorScheme", scheme_name)
    parser_dst.set("General", "Name", "Catppuccin Mocha Lavender" if using_official_catppuccin else "Caelestia")
    parser_dst.set("General", "shadeSortColumn", "true")

    # KDE preferences
    if not parser_dst.has_section("KDE"):
        parser_dst.add_section("KDE")
    if parser_dst.has_option("KDE", "LookAndFeelPackage"):
        parser_dst.remove_option("KDE", "LookAndFeelPackage")
    parser_dst.set("KDE", "ColorScheme", scheme_name)
    parser_dst.set("KDE", "widgetStyle", "darkly")
    parser_dst.set("KDE", "contrast", "4")
    parser_dst.set("KDE", "SingleClick", "false")

    # Icon theme: prefer Colloid-Catppuccin-Dark, fallback to Papirus-Dark, then breeze-dark
    colloid_path = Path.home() / ".local/share/icons/Colloid-Catppuccin-Dark"
    papirus_paths = [
        Path("/usr/share/icons/Papirus-Dark"),
        Path.home() / ".local/share/icons/Papirus-Dark"
    ]
    if colloid_path.exists():
        icon_theme = "Colloid-Catppuccin-Dark"
    elif any(p.exists() for p in papirus_paths):
        icon_theme = "Papirus-Dark"
    else:
        icon_theme = "breeze-dark"

    if not parser_dst.has_section("Icons"):
        parser_dst.add_section("Icons")
    parser_dst.set("Icons", "Theme", icon_theme)

    # Write kdeglobals atomically
    tmp_path = KDEGLOBALS.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        parser_dst.write(f, space_around_delimiters=False)
    os.replace(tmp_path, KDEGLOBALS)

    # Write QtEngine colors in hex
    hex_parser = configparser.ConfigParser(interpolation=None)
    hex_parser.optionxform = str
    for section in parser_dst.sections():
        hex_parser.add_section(section)
        for k, v in parser_dst.items(section):
            if ',' in v and not k.lower().endswith('font'):
                v = rgb_to_hex(v)
            hex_parser.set(section, k, v)
    with open(CAELESTIA_COLORS, "w") as f:
        hex_parser.write(f, space_around_delimiters=False)

    # Also register Caelestia.colors in ~/.local/share/color-schemes/
    COLOR_SCHEMES_DIR.mkdir(parents=True, exist_ok=True)
    with open(CAELESTIA_KDE_SCHEME, "w") as f:
        parser_dst.write(f, space_around_delimiters=False)

    print(f"[sync-dolphin] Successfully updated {KDEGLOBALS} with {'authentic Catppuccin Mocha' if using_official_catppuccin else 'Caelestia scheme'}")

    # Notify DBus
    try:
        subprocess.run(
            ["dbus-send", "--type=signal", "/KGlobalSettings", "org.kde.KGlobalSettings.notifyChange", "int32:0", "int32:0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
    except Exception:
        pass

if __name__ == "__main__":
    sync()
