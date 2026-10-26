#!/bin/sh
# Toggle a "quiet" shell state: close every open caelestia drawer and force DnD
# on, so nothing can draw over or interrupt a fullscreen app. Second press
# restores DnD to whatever it was before.
set -eu

state="${XDG_RUNTIME_DIR:-/tmp}/caelestia-quiet"
ipc() { qs -c caelestia ipc call "$@" >/dev/null 2>&1 || true; }

if [ -f "$state" ]; then
    # Restore: put DnD back to the value recorded on the way in.
    [ "$(cat "$state")" = "true" ] || ipc notifs disableDnd
    rm -f "$state"
else
    # Record DnD so we don't clobber it, then close everything and silence.
    qs -c caelestia ipc call notifs isDndEnabled 2>/dev/null > "$state" || echo false > "$state"
    for d in sidebar dashboard utilities osd session launcher; do
        [ "$(qs -c caelestia ipc call drawers isOpen "$d" 2>/dev/null)" = "1" ] \
            && ipc drawers toggle "$d"
    done
    ipc notifs enableDnd
fi
