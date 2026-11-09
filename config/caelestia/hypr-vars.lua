local scheme = require("scheme.current")

return {
    workspaceSwipeFingers = 3,

    -- Compact tiling: gaps_in is applied on both sides of adjacent windows.
    windowGapsIn = 1,
    windowGapsOut = 1,
    singleWindowGapsOut = 1,

    -- Nest inside the shell's 25px curve (2px frame + 1px outer gap).
    windowRounding = 14,
    windowBorderSize = 2,
    activeWindowBorderColour = "rgba(" .. scheme.primary .. "88)",

    -- Performance optimizations:
    -- Lighter blur (1 pass, smaller radius) reduces fillrate on 120Hz display
    blurPasses = 1,
    blurSize = 4,
    blurPopups = false,

    -- Lighter shadows
    shadowRange = 6,
    shadowRenderPower = 2,
}
