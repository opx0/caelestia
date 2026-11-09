pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Caelestia.Config
import Caelestia.I18n
import qs.components
import qs.services

Item {
    id: root

    readonly property string timeText: {
        const minutes = Math.floor(TimerService.remainingSeconds / 60).toString().padStart(2, "0");
        const seconds = (TimerService.remainingSeconds % 60).toString().padStart(2, "0");
        return `${minutes}:${seconds}`;
    }

    implicitWidth: content.implicitWidth
    implicitHeight: content.implicitHeight

    RowLayout {
        id: content

        anchors.centerIn: parent
        spacing: Tokens.spacing.small

        MaterialIcon {
            Layout.alignment: Qt.AlignVCenter
            text: TimerService.finished ? "timer_off" : (TimerService.running ? "timer" : "pause_circle")
            color: TimerService.finished ? Colours.palette.m3error : Colours.palette.m3tertiary
            fontStyle: Tokens.font.icon.small
        }

        StyledText {
            Layout.alignment: Qt.AlignVCenter
            text: root.timeText
            font: Qt.font({ family: "Pixelon", pixelSize: 22, weight: Font.Normal, letterSpacing: 1 })
            color: TimerService.finished ? Colours.palette.m3error : Colours.tPalette.m3onSurface
        }

        StyledText {
            Layout.alignment: Qt.AlignVCenter
            visible: TimerService.finished
            text: Tr.tr("Done")
            font: Tokens.font.body.builders.small.weight(Font.Medium).build()
            color: Colours.palette.m3error
        }
    }
}
