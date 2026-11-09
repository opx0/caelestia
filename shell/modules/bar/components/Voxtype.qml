pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Caelestia.Config
import Caelestia.I18n
import qs.components
import qs.services

Item {
    id: root

    readonly property int columns: 29
    readonly property int rows: 7
    readonly property int middleRow: Math.floor(rows / 2)
    readonly property color waveColour: Colours.palette.m3tertiary
    property var samples: new Array(180).fill(0)

    readonly property bool recording: VoxtypeService.recording
    readonly property bool transcribing: VoxtypeService.transcribing
    readonly property bool complete: VoxtypeService.complete
    readonly property string elapsed: {
        const minutes = Math.floor(VoxtypeService.elapsedSeconds / 60).toString().padStart(2, "0");
        const seconds = (VoxtypeService.elapsedSeconds % 60).toString().padStart(2, "0");
        return `${minutes}:${seconds}`;
    }

    function clearSamples(): void {
        samples = new Array(180).fill(0);
        waveform.requestPaint();
    }

    function pushFrame(peak: real): void {
        const next = samples.slice(1);
        next.push(peak);
        samples = next;
    }

    implicitWidth: content.implicitWidth
    implicitHeight: Math.max(Tokens.sizes.bar.innerWidth - Tokens.padding.small, content.implicitHeight)

    onRecordingChanged: if (recording) clearSamples()

    VoxtypeAudioBridge {
        enabled: root.recording

        onFrameReceived: function(peak, rms, vad, tsMs) {
            root.pushFrame(peak);
        }

        onDisconnected: root.clearSamples()
    }

    RowLayout {
        id: content

        anchors.centerIn: parent
        spacing: Tokens.spacing.small

        Loader {
            Layout.alignment: Qt.AlignVCenter
            active: root.recording
            visible: active

            sourceComponent: Rectangle {
                width: 8
                height: 8
                radius: width / 2
                color: Colours.palette.m3error
            }
        }

        Item {
            Layout.alignment: Qt.AlignVCenter
            implicitWidth: root.columns * 4
            implicitHeight: root.rows * 4
            visible: root.recording

            Canvas {
                id: waveform

                function levelForColumn(column: int): real {
                    const first = Math.floor(column * root.samples.length / root.columns);
                    const last = Math.floor((column + 1) * root.samples.length / root.columns);
                    let peak = 0;
                    for (let i = first; i < last; i++)
                        peak = Math.max(peak, root.samples[i]);
                    if (peak <= 0)
                        return 0;

                    const dbfs = 20 * Math.log10(peak);
                    return dbfs <= -42 ? 0 : Math.min(1, (dbfs + 42) / 42);
                }

                anchors.centerIn: parent
                width: root.columns * 4
                height: root.rows * 4
                antialiasing: true

                onPaint: {
                    const context = getContext("2d");
                    context.clearRect(0, 0, width, height);

                    for (let column = 0; column < root.columns; column++) {
                        const litRows = Math.round(levelForColumn(column) * root.middleRow);
                        for (let row = 0; row < root.rows; row++) {
                            const distance = Math.abs(row - root.middleRow);
                            const lit = distance > 0 && distance <= litRows;
                            const alpha = lit ? 0.95 : (distance === 0 ? 0.38 : 0.12);

                            context.beginPath();
                            context.fillStyle = Qt.rgba(root.waveColour.r, root.waveColour.g, root.waveColour.b, alpha);
                            context.arc(column * 4 + 2, row * 4 + 2, 1.4, 0, Math.PI * 2);
                            context.fill();
                        }
                    }
                }
            }

            Timer {
                interval: 33
                repeat: true
                running: root.recording
                onTriggered: waveform.requestPaint()
            }
        }

        StyledText {
            Layout.alignment: Qt.AlignVCenter
            visible: root.recording
            text: root.elapsed
            font: Tokens.font.body.builders.small.weight(Font.Medium).build()
            color: root.waveColour
        }

        Loader {
            Layout.alignment: Qt.AlignVCenter
            active: root.transcribing || root.complete
            visible: active

            sourceComponent: MaterialIcon {
                text: root.complete ? "check_circle" : "progress_activity"
                color: root.waveColour
                fontStyle: Tokens.font.icon.small

                RotationAnimation on rotation {
                    from: 0
                    to: 360
                    duration: 900
                    loops: Animation.Infinite
                    running: root.transcribing
                }
            }
        }

        StyledText {
            Layout.alignment: Qt.AlignVCenter
            visible: root.transcribing || root.complete
            text: root.complete ? Tr.tr("Complete") : Tr.tr("Transcribing…")
            font: Tokens.font.body.builders.small.weight(Font.Medium).build()
            color: root.waveColour
        }
    }
}
