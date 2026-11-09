pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts
import Caelestia.Config
import Caelestia.I18n
import qs.components
import qs.components.controls
import qs.services
import qs.modules.nexus.common

PageBase {
    id: root

    function pluginSubtext(plugin: var): string {
        const status = plugin.failed ? Tr.tr("Failed to build") : plugin.enabled ? Tr.tr("Enabled") : Tr.tr("Disabled");
        return plugin.repository ? Tr.tr("%1 · %2").arg(status).arg(plugin.repository) : status;
    }

    title: Tr.tr("Plugins")

    ColumnLayout {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        width: root.cappedWidth
        spacing: Tokens.spacing.extraSmall / 2

        // Installed plugins
        RowLayout {
            Layout.fillWidth: true
            Layout.bottomMargin: Tokens.spacing.extraSmall
            spacing: Tokens.spacing.medium

            StyledText {
                Layout.fillWidth: true
                Layout.leftMargin: Tokens.padding.small
                text: Tr.tr("Installed plugins")
                color: Colours.palette.m3onSurfaceVariant
                font: Tokens.font.label.medium
                elide: Text.ElideRight
            }

            IconTextButton {
                type: IconTextButton.Text
                icon: "refresh"
                text: Tr.tr("Refresh")
                font: Tokens.font.label.medium
                horizontalPadding: Tokens.padding.small
                verticalPadding: Tokens.padding.extraSmall
                disabled: Hyprpm.loading || Hyprpm.busy
                onClicked: Hyprpm.refresh()
            }
        }

        StyledText {
            Layout.fillWidth: true
            Layout.leftMargin: Tokens.padding.small
            visible: !Hyprpm.available
            text: Tr.tr("HyprPM was not found. It ships with Hyprland and is required to manage plugins.")
            color: Colours.palette.m3outline
            font: Tokens.font.body.small
            wrapMode: Text.WordWrap
        }

        StyledText {
            Layout.fillWidth: true
            Layout.leftMargin: Tokens.padding.small
            visible: Hyprpm.available && !Hyprpm.loaded
            text: Tr.tr("Loading plugins…")
            color: Colours.palette.m3outline
            font: Tokens.font.body.small
            wrapMode: Text.WordWrap
        }

        StyledText {
            Layout.fillWidth: true
            Layout.leftMargin: Tokens.padding.small
            visible: Hyprpm.available && Hyprpm.loaded && Hyprpm.installedCount === 0
            text: Tr.tr("No HyprPM plugins are installed.")
            color: Colours.palette.m3outline
            font: Tokens.font.body.small
            wrapMode: Text.WordWrap
        }

        Repeater {
            model: Hyprpm.plugins

            ToggleRow {
                required property var modelData
                required property int index

                first: index === 0
                last: index === Hyprpm.plugins.length - 1
                text: modelData.name
                subtext: root.pluginSubtext(modelData)
                checked: modelData.enabled
                disabled: Hyprpm.busy || modelData.failed
                onToggled: Hyprpm.setEnabled(modelData, checked)
            }
        }

        StyledText {
            Layout.fillWidth: true
            Layout.leftMargin: Tokens.padding.small
            visible: Hyprpm.lastError.length > 0
            text: Hyprpm.lastError
            color: Colours.palette.m3error
            font: Tokens.font.label.small
            wrapMode: Text.WordWrap
        }

        // HyprPM
        SectionHeader {
            text: Tr.tr("HyprPM")
        }

        NavRow {
            first: true
            last: true
            icon: "refresh"
            text: Tr.tr("Reload plugins")
            subtext: {
                const base = Tr.tr("%1 installed · %2 enabled").arg(Hyprpm.installedCount).arg(Hyprpm.enabledCount);
                return Hyprpm.failedCount > 0 ? Tr.tr("%1 · %2 failed").arg(base).arg(Hyprpm.failedCount) : base;
            }
            disabled: Hyprpm.busy || !Hyprpm.available
            onClicked: Hyprpm.reload()
        }
    }
}
