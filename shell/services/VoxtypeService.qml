pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    readonly property string runtimeDir: Quickshell.env("XDG_RUNTIME_DIR") || `/run/user/${Quickshell.env("UID") || "1000"}`
    readonly property string statePath: Quickshell.env("CAELESTIA_VOXTYPE_STATE") || `${runtimeDir}/voxtype/state`
    property string state: "idle"
    property string rawState: "idle"
    property int elapsedSeconds: 0

    readonly property bool recording: state === "recording" || state === "streaming"
    readonly property bool transcribing: state === "transcribing"
    readonly property bool complete: state === "complete"
    readonly property bool active: recording || transcribing || complete

    function updateState(value: string): void {
        const next = ["idle", "recording", "streaming", "transcribing", "stopped"].includes(value) ? value : "idle";

        if ((rawState === "transcribing" || rawState === "streaming") && next === "idle") {
            state = "complete";
            completionTimer.restart();
        } else {
            completionTimer.stop();
            state = next;
        }

        const wasRecording = rawState === "recording" || rawState === "streaming";
        const isRecording = next === "recording" || next === "streaming";
        if (isRecording && !wasRecording)
            elapsedSeconds = 0;

        rawState = next;
    }

    FileView {
        id: stateFile

        path: root.statePath
        watchChanges: true
        printErrors: false

        onLoaded: root.updateState(text().trim())
        onFileChanged: reload()
        onLoadFailed: root.updateState("idle")
    }

    Timer {
        interval: 1000
        running: root.state === "idle" && root.statePath.length > 0
        repeat: true
        onTriggered: stateFile.reload()
    }

    Timer {
        id: recordingTimer

        interval: 1000
        repeat: true
        running: root.recording
        onTriggered: root.elapsedSeconds++
    }

    Timer {
        id: completionTimer

        interval: 1400
        onTriggered: root.state = root.rawState
    }
}
