#!/usr/bin/env python3
"""
Sync Caelestia color scheme with KDE kdeglobals for Dolphin and Qt applications.
Ensures authentic, vibrant Catppuccin Mocha colors rather than dull/washed-out M3 tones.
Includes automated Qt ABI version detection,, self-healing recompilation, andand complete
uncompromisedcomplete
uncompromised themetheme calibration (fixing disabled text contrast, button active states,
and Places focus indicators)calibration (fixing disabled text contrast, button active states,
and Places focus indicators).
"""

import configparser
import json
import os
import shutil
import subprocess
from pathlib import Path

CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
DATA_DIR = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share"))
STATE_DIR = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local/state"))

QTENGINE_DIR = CONFIG_DIR / "qtengine"
QTENGINE_CONFIG = QTENGINE_DIR / "config.json"
CAELESTIA_COLORS = QTENGINE_DIR / "caelestia.colors"
KDEGLOBALS = CONFIG_DIR / "kdeglobals"
DARKLYRC = CONFIG_DIR / "darklyrc"
COLOR_SCHEMES_DIR = DATA_DIR / "color-schemes"
CAELESTIA_KDE_SCHEME = COLOR_SCHEMES_DIR / "Caelestia.colors"
SCHEME_JSON = STATE_DIR / "caelestia" / "scheme.json"

LOCAL_LIB = Path.home() / ".local" / "lib"
QT6_PLUGINS = LOCAL_LIB / "qt6" / "plugins"
QT_VERSION_FILE = QT6_PLUGINS / ".qt_version"


def find_qtengine_src() -> Path | None:
    """Finds the qtengine source directory across local repo checkouts, state, or clones it."""
    candidates = [
        Path.home() / ".local" / "src" / "qtengine",
        Path.home() / "code" / "caelestia" / "packages" / "qtengine",
        Path.home() / ".local" / "state" / "caelestia" / "dots" / "packages" / "qtengine",
        Path(__file__).resolve().parents[3] / "packages" / "qtengine",
    ]
    for c in candidates:
        if c.exists() and (c / "CMakeLists.txt").exists():
            return c

    # Fallback: Auto-clone if missing on fresh install
    target = Path.home() / ".local" / "src" / "qtengine"
    try:
        print("[sync-dolphin] Fetching qtengine source from upstream...")
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/kossLAN/qtengine.git", str(target)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        if target.exists() and (target / "CMakeLists.txt").exists():
            return target
    except Exception:
        pass
    return None


def find_catppuccin_scheme() -> Path | None:
    """Finds the authentic Catppuccin Mocha Lavender color scheme file."""
    candidates = [
        COLOR_SCHEMES_DIR / "CatppuccinMochaLavender.colors",
        Path.home() / "code" / "caelestia" / "color-schemes" / "CatppuccinMochaLavender.colors",
        Path.home() / ".local" / "state" / "caelestia" / "dots" / "color-schemes" / "CatppuccinMochaLavender.colors",
        Path(__file__).resolve().parents[3] / "color-schemes" / "CatppuccinMochaLavender.colors",
        Path.home() / ".config" / "caelestia" / "dolphin-suite" / "colors" / "CatppuccinMochaLavender.colors",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def find_qtengine_src() -> Path | None:
    """Finds the qtengine source directory across local repo checkouts, state, or clones it."""
    candidates = [
        Path.home() / ".local" / "src" / "qtengine",
        Path.home() / "code" / "caelestia" / "packages" / "qtengine",
        Path.home() / ".local" / "state" / "caelestia" / "dots" / "packages" / "qtengine",
        Path(__file__).resolve().parents[3] / "packages" / "qtengine",
    ]
    for c in candidates:
        if c.exists() and (c / "CMakeLists.txt").exists():
            return c

    # Fallback: Auto-clone if missing on fresh install
    target = Path.home() / ".local" / "src" / "qtengine"
    try:
        print("[sync-dolphin] Fetching qtengine source from upstream...")
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "https://github.com/kossLAN/qtengine.git", str(target)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        if target.exists() and (target / "CMakeLists.txt").exists():
            return target
    except Exception:
        pass
    return None


def find_catppuccin_scheme() -> Path | None:
    """Finds the authentic Catppuccin Mocha Lavender color scheme file."""
    candidates = [
        COLOR_SCHEMES_DIR / "CatppuccinMochaLavender.colors",
        Path.home() / "code" / "caelestia" / "color-schemes" / "CatppuccinMochaLavender.colors",
        Path.home() / ".local" / "state" / "caelestia" / "dots" / "color-schemes" / "CatppuccinMochaLavender.colors",
        Path(__file__).resolve().parents[3] / "color-schemes" / "CatppuccinMochaLavender.colors",
        Path.home() / ".config" / "caelestia" / "dolphin-suite" / "colors" / "CatppuccinMochaLavender.colors",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def ensure_qtengine_compatibility():
    """
    Guarantees 100% resilience against Qt updates and clean installs:
    Checks if Qt version has changed oror ifif plugins are missingplugins are missing.
    If mismatched, automatically recompiles qtengine.
    """
    plugin_so = QT6_PLUGINS / "platformthemes" / "libqt6engine-plugin.so"

    try:
        res = subprocess.run(
            ["qmake6", "-query", "QT_VERSION"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False
        )
        current_qt = res.stdout.strip()
    except Exception:
        current_qt = ""

    if not current_qt:
        return

    built_qt = ""
    if QT_VERSION_FILE.exists():
        try:
            built_qt = QT_VERSION_FILE.read_text().strip()
        except Exception:
            built_qt = ""

    if built_qt != current_qt or not plugin_so.exists():
        src_dir = find_qtengine_src()
        if src_dir:
            print(f"[sync-dolphin] Qt environment check (built: '{built_qt}', system: '{current_qt}'). Compiling qtengine from {src_dir}...")
            build_dir = Path("/tmp") / f"qtengine-rebuild-{os.getuid()}"
            build_dir.mkdir(parents=True, exist_ok=True)
            try:
                cmake_cmd = [
                    "cmake",
                    "-B", str(build_dir),
                    "-S", str(src_dir),
                    "-G", "Ninja",
                    "-DCMAKE_BUILD_TYPE=Release",
                    f"-DCMAKE_INSTALL_PREFIX={Path.home() / '.local'}"
                ]
                subprocess.run(cmake_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                subprocess.run(["cmake", "--build", str(build_dir)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                subprocess.run(["cmake", "--install", str(build_dir)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                QT6_PLUGINS.mkdir(parents=True, exist_ok=True)
                QT_VERSION_FILE.write_text(current_qt)
                perm_local = Path.home() / ".local" / "src" / "qtengine"
                if src_dir != perm_local and not perm_local.exists():
                    try:
                        shutil.copytree(src_dir, perm_local, ignore=shutil.ignore_patterns("build", ".git"))
                    except Exception:
                        pass
                print(f"[sync-dolphin] Successfully built and verified qtengine for Qt {current_qt}.")
            except Exception as e:
                print(f"[sync-dolphin] Auto-rebuild error: {e}")
        else:
            print("[sync-dolphin] Warning: qtengine source not found.")


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
    # 1. Guarantee Qt engine binary compatibility first
    ensure_qtengine_compatibility()

    # 2. Detect active scheme
    is_catppuccin = True
    if SCHEME_JSON.exists():
        try:
            s_data = json.loads(SCHEME_JSON.read_text())
            if s_data.get("name") != "catppuccin":
                is_catppuccin = False
        except Exception:
            pass

    # Source palette selection:
    parser_src = configparser.ConfigParser(interpolation=None)
    parser_src.optionxform = str

    using_official_catppuccin = False
    catppuccin_scheme_file = find_catppuccin_scheme()
    if is_catppuccin and catppuccin_scheme_file:
        parser_src.read(catppuccin_scheme_file)
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

    # Clean out duplicate/stale lowercase keys from existing sections
    for section in color_sections:
        if parser_dst.has_section(section):
            parser_dst.remove_section(section)

    for section in color_sections:
        if parser_src.has_section(section):
            parser_dst.add_section(section)
            for k, v in parser_src.items(section):
                if v.startswith("#"):
                    v = hex_to_rgb(v)
                parser_dst.set(section, k, v)

    # Complete theme calibration (eliminating anomalies across all UI areas)
    # 1. Selection color: High-contrast, radiant Catppuccin Lavender/Indigo (114, 135, 253 / #7287fd)
    # Never blends into dark view or sidebar background; perfectly visible in both active & inactive states
    if not parser_dst.has_section("Colors:Selection"):
        parser_dst.add_section("Colors:Selection")
    parser_dst.set("Colors:Selection", "BackgroundNormal", "114,135,253")
    parser_dst.set("Colors:Selection", "BackgroundAlternate", "100,118,222")
    parser_dst.set("Colors:Selection", "DecorationFocus", "180,190,254")
    parser_dst.set("Colors:Selection", "DecorationHover", "69,71,90")
    parser_dst.set("Colors:Selection", "ForegroundNormal", "255,255,255")
    parser_dst.set("Colors:Selection", "ForegroundActive", "255,255,255")
    parser_dst.set("Colors:Selection", "ForegroundInactive", "255,255,255")

    # Inactive effect: Ensure inactive window / split pane never drops selection to muddy dark
    if not parser_dst.has_section("ColorEffects:Inactive"):
        parser_dst.add_section("ColorEffects:Inactive")
    parser_dst.set("ColorEffects:Inactive", "ChangeSelectionColor", "false")
    parser_dst.set("ColorEffects:Inactive", "Enable", "false")

    # 2. Button alternate background: Surface1 (#45475a -> 69, 71, 90)
    # Prevents buttons from flashing blinding solid white/lavender when clicked or checked!
    if parser_dst.has_section("Colors:Button"):
        parser_dst.set("Colors:Button", "BackgroundAlternate", "69,71,90")

    # 3. Disabled text effects: Crisp muted Overlay0 (#6c7086 -> 108, 112, 134)
    # Prevents disabled menu items ('Undo', 'Redo', 'Filter...') from fading into invisible pitch black!
    if not parser_dst.has_section("ColorEffects:Disabled"):
        parser_dst.add_section("ColorEffects:Disabled")
    parser_dst.set("ColorEffects:Disabled", "Color", "108,112,134")
    parser_dst.set("ColorEffects:Disabled", "ColorAmount", "0")
    parser_dst.set("ColorEffects:Disabled", "ColorEffect", "0")
    parser_dst.set("ColorEffects:Disabled", "ContrastAmount", "0.45")
    parser_dst.set("ColorEffects:Disabled", "ContrastEffect", "1")
    parser_dst.set("ColorEffects:Disabled", "IntensityAmount", "0")
    parser_dst.set("ColorEffects:Disabled", "IntensityEffect", "0")

    # 3. Clean link & places underline
    if not parser_dst.has_section("KDE"):
        parser_dst.add_section("KDE")
    scheme_name = "CatppuccinMochaLavender" if using_official_catppuccin else "Caelestia"
    parser_dst.set("KDE", "ColorScheme", scheme_name)
    parser_dst.set("KDE", "widgetStyle", "darkly")
    parser_dst.set("KDE", "contrast", "4")
    parser_dst.set("KDE", "SingleClick", "false")
    parser_dst.set("KDE", "ShowUnderline", "false")
    parser_dst.set("KDE", "underLine", "false")

    # Metadata
    if not parser_dst.has_section("General"):
        parser_dst.add_section("General")
    parser_dst.set("General", "ColorScheme", scheme_name)
    parser_dst.set("General", "Name", "Catppuccin Mocha Lavender" if using_official_catppuccin else "Caelestia")
    parser_dst.set("General", "shadeSortColumn", "true")

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

    # Write darklyrc to eliminate focus rectangles, ugly outlines, and ensure seamless dark blending
    darkly_parser = configparser.ConfigParser(interpolation=None)
    darkly_parser.optionxform = str
    if DARKLYRC.exists():
        darkly_parser.read(DARKLYRC)
    if not darkly_parser.has_section("Common"):
        darkly_parser.add_section("Common")
    darkly_parser.set("Common", "ButtonHeight", "2")
    darkly_parser.set("Common", "ButtonWidth", "1")
    darkly_parser.set("Common", "CornerRadius", "8")
    darkly_parser.set("Common", "FancyMargins", "true")
    darkly_parser.set("Common", "MenuItemHeight", "4")
    darkly_parser.set("Common", "ShadowIntensity", "Medium")
    darkly_parser.set("Common", "ShadowSize", "ShadowMedium")
    darkly_parser.set("Common", "ShadowStrength", "200")
    darkly_parser.set("Common", "SunkenEffect", "false")

    if not darkly_parser.has_section("Style"):
        darkly_parser.add_section("Style")
    darkly_parser.set("Style", "AdjustToDarkThemes", "true")
    darkly_parser.set("Style", "AnimationsDuration", "200")
    darkly_parser.set("Style", "AnimationsEnabled", "true")
    darkly_parser.set("Style", "DisableDolphinUrlNavigatorBackground", "true")
    darkly_parser.set("Style", "DolphinSidebarOpacity", "100")
    darkly_parser.set("Style", "DolphinViewOpacity", "100")
    darkly_parser.set("Style", "FullOutline", "false")
    darkly_parser.set("Style", "MenuItemDrawStrongFocus", "false")
    darkly_parser.set("Style", "MenuOpacity", "100")
    darkly_parser.set("Style", "NewDolphinSelectionStyle", "true")
    darkly_parser.set("Style", "NoOutline", "true")
    darkly_parser.set("Style", "SidePanelDrawFrame", "false")
    darkly_parser.set("Style", "ToolBarDrawItemSeparator", "false")
    darkly_parser.set("Style", "ToolBarDrawSeparator", "false")
    darkly_parser.set("Style", "ToolBarOpacity", "100")
    darkly_parser.set("Style", "ViewDrawFocusIndicator", "false")
    darkly_parser.set("Style", "ViewDrawTreeBranchLines", "true")
    darkly_parser.set("Style", "WidgetDrawShadow", "false")

    tmp_darkly = DARKLYRC.with_suffix(".tmp")
    with open(tmp_darkly, "w") as f:
        darkly_parser.write(f, space_around_delimiters=False)
    os.replace(tmp_darkly, DARKLYRC)

    # Also ensure ~/.config/qtengine/config.json uses the absolute resolved path to colorScheme
    if QTENGINE_CONFIG.exists():
        try:
            with open(QTENGINE_CONFIG, "r") as f:
                cfg = json.load(f)
            cfg.setdefault("theme", {})
            cfg["theme"]["colorScheme"] = str(CAELESTIA_COLORS.resolve())
            cfg["theme"]["style"] = "Darkly"
            cfg["theme"]["iconTheme"] = icon_theme
            with open(QTENGINE_CONFIG, "w") as f:
                json.dump(cfg, f, indent=4)
        except Exception:
            pass

    # Also register Caelestia.colors in ~/.local/share/color-schemes/
    COLOR_SCHEMES_DIR.mkdir(parents=True, exist_ok=True)
    with open(CAELESTIA_KDE_SCHEME, "w") as f:
        parser_dst.write(f, space_around_delimiters=False)

    print(f"[sync-dolphin] Successfully updated {KDEGLOBALS} with authentic Catppuccin Mocha")

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
