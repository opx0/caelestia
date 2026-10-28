#!/bin/sh
marker="${XDG_RUNTIME_DIR:-/tmp}/caelestia-opaque-mode"
if [ -e "$marker" ]; then
    rm -f "$marker"
    message="Window transparency enabled"
else
    : > "$marker"
    message="Window transparency disabled"
fi
hyprctl reload >/dev/null && notify-send "Transparency" "$message"
