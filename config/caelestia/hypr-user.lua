-- >>> timestack >>>
hl.bind("XF86Calculator", hl.dsp.exec_cmd("/home/opx/Archive/csAssist/timestack/capture.sh"))
hl.bind("KP_Subtract", hl.dsp.exec_cmd("/home/opx/Archive/csAssist/timestack/capture.sh codex"))
hl.bind("KP_Divide", hl.dsp.exec_cmd("/usr/bin/python3 /home/opx/Archive/csAssist/timestack/timestack.py type solution"))
hl.bind("KP_Multiply", hl.dsp.exec_cmd("/usr/bin/python3 /home/opx/Archive/csAssist/timestack/timestack.py stop"))
-- <<< timestack <<<

-- >>> quiet toggle >>>
-- SUPER + SHIFT + N: close all caelestia drawers + force DnD, press again to restore.
-- SUPER + N already toggles the sidebar on its own (vars.kbShowSidebar).
hl.bind("SUPER + SHIFT + N", hl.dsp.exec_cmd("/home/opx/.config/caelestia/quiet-toggle.sh"))
-- <<< quiet toggle <<<

-- >>> dolphin integration >>>
hl.window_rule({ match = { class = "org.kde.dolphin", title = "(Copying|Moving|Deleting|Progress|Overwrite|Properties)" }, float = true, center = true })
-- <<< dolphin integration <<<

