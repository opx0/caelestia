pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io

Item {
    id: root

    property bool enabled: false
    property string bridgeBinary: "voxtype-audio-bridge"
    property int restartDelayMs: 1000
    property bool connected: false
    property real peak: 0
    property real rms: 0
    property bool vad: false

    signal frameReceived(real peak, real rms, bool vad, var tsMs)
    signal disconnected()

    function handleLine(line: string): void {
        const trimmed = line.trim();
        if (!trimmed)
            return;

        let data;
        try {
            data = JSON.parse(trimmed);
        } catch (error) {
            console.warn("Voxtype audio bridge returned invalid JSON:", trimmed);
            return;
        }

        if (data.status === "connected") {
            connected = true;
            return;
        }

        if (data.status === "disconnected") {
            if (connected) {
                connected = false;
                root.disconnected();
            }
            return;
        }

        if (typeof data.peak === "number" && typeof data.rms === "number") {
            peak = data.peak;
            rms = data.rms;
            vad = !!data.vad;
            connected = true;
            root.frameReceived(peak, rms, vad, data.ts_ms ?? 0);
        }
    }

    onEnabledChanged: {
        restartTimer.stop();
        bridge.running = enabled;
    }

    Component.onCompleted: if (enabled) bridge.running = true

    Process {
        id: bridge

        command: [root.bridgeBinary]
        running: false

        stdout: SplitParser {
            splitMarker: "\n"
            onRead: data => root.handleLine(data)
        }

        onRunningChanged: {
            if (bridge.running)
                return;
            if (root.connected) {
                root.connected = false;
                root.disconnected();
            }
            if (root.enabled)
                restartTimer.restart();
        }
    }

    Timer {
        id: restartTimer

        interval: root.restartDelayMs
        onTriggered: {
            if (root.enabled && !bridge.running)
                bridge.running = true;
        }
    }
}
