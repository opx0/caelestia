pragma Singleton

import QtQuick
import Quickshell
import Quickshell.Io

Singleton {
    id: root

    property bool active: false
    property bool running: false
    property bool finished: false
    property int remainingSeconds: 0
    property double deadline: 0
    property int pausedSeconds: 0

    function start(seconds: int): void {
        if (seconds <= 0) {
            console.warn("Timer duration must be greater than zero seconds");
            return;
        }
        finishedTimer.stop();
        active = true;
        finished = false;
        running = true;
        remainingSeconds = seconds;
        deadline = Date.now() + seconds * 1000;
        tick.restart();
    }

    function pause(): void {
        if (!running)
            return;
        pausedSeconds = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
        remainingSeconds = pausedSeconds;
        running = false;
        tick.stop();
    }

    function resume(): void {
        if (!active || running || finished || pausedSeconds <= 0)
            return;
        deadline = Date.now() + pausedSeconds * 1000;
        running = true;
        tick.restart();
    }

    function toggle(): void {
        if (running)
            pause();
        else
            resume();
    }

    function reset(): void {
        tick.stop();
        finishedTimer.stop();
        running = false;
        finished = false;
        active = false;
        remainingSeconds = 0;
        pausedSeconds = 0;
    }

    IpcHandler {
        function start(seconds: int): void { root.start(seconds); }
        function pause(): void { root.pause(); }
        function resume(): void { root.resume(); }
        function toggle(): void { root.toggle(); }
        function reset(): void { root.reset(); }
        function dismiss(): void { root.reset(); }

        target: "timer"
    }

    Timer {
        id: tick

        interval: 200
        repeat: true
        onTriggered: {
            const seconds = Math.max(0, Math.ceil((root.deadline - Date.now()) / 1000));
            root.remainingSeconds = seconds;
            root.pausedSeconds = seconds;
            if (seconds === 0) {
                stop();
                root.running = false;
                root.finished = true;
                finishedTimer.start();
            }
        }
    }

    Timer {
        id: finishedTimer

        interval: 1200
        onTriggered: root.reset()
    }
}
