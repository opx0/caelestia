pragma ComponentBehavior: Bound

import QtQuick
import Caelestia.Config
import qs.components
import qs.services

StyledRect {
    id: root

    required property bool isHorizontal

    readonly property var contexts: [
        {
            id: "voxtype",
            priority: 100,
            active: root.isHorizontal && VoxtypeService.active,
            component: voxtypeContent
        },
        {
            id: "timer",
            priority: 80,
            active: root.isHorizontal && TimerService.active,
            component: timerContent
        },
        {
            id: "clock",
            priority: 0,
            active: true,
            component: clockContent
        }
    ]
    readonly property var currentContext: contexts.filter(context => context.active).sort((a, b) => b.priority - a.priority)[0]
    readonly property bool hasContext: currentContext.id !== "clock"
    readonly property bool raisedContext: currentContext.id === "voxtype"
    readonly property real contentWidth: content.implicitWidth

    implicitWidth: isHorizontal ? contentWidth + (raisedContext ? Tokens.padding.medium * 2 : 0) : Tokens.sizes.bar.innerWidth
    implicitHeight: isHorizontal ? Tokens.sizes.bar.innerWidth + (raisedContext ? Tokens.padding.medium : 0) : content.implicitHeight + (hasContext ? Tokens.padding.medium * 2 : 0)

    color: raisedContext ? Qt.alpha(Colours.tPalette.m3surfaceContainer, 0.38) : "transparent"
    radius: Tokens.rounding.full

    Behavior on implicitWidth {
        Anim {
            type: Anim.Emphasized
        }
    }

    Behavior on implicitHeight {
        Anim {
            type: Anim.Emphasized
        }
    }

    Loader {
        id: content

        anchors.centerIn: parent
        sourceComponent: root.currentContext.component
    }

    Component {
        id: clockContent

        Clock {
            isHorizontal: root.isHorizontal
        }
    }

    Component {
        id: voxtypeContent

        Voxtype {}
    }

    Component {
        id: timerContent

        TimerIsland {}
    }
}
