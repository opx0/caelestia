pragma ComponentBehavior: Bound

import QtQuick
import Quickshell.Io
import Caelestia.Config
import qs.components
import qs.services

Flickable {
    id: root

    property var providers: []
    property string error: "Loading cached quota..."
    property string executable: "/home/opx/.local/bin/aiquota"

    function readCache(): void {
        if (!reader.running)
            reader.running = true;
    }

    function displayTime(value: var): string {
        if (!value)
            return "Reset unknown";
        const date = new Date(value);
        return isNaN(date.getTime()) ? "Reset unknown" : "Resets " + date.toLocaleString();
    }

    implicitWidth: 320
    implicitHeight: Math.min(contentColumn.implicitHeight, 460)
    contentWidth: width
    contentHeight: contentColumn.implicitHeight
    clip: true
    boundsBehavior: Flickable.StopAtBounds

    Component.onCompleted: readCache()

    Timer {
        interval: 30000
        running: true
        repeat: true
        onTriggered: root.readCache()
    }

    Process {
        id: reader
        command: [root.executable, "status", "--cached", "--json"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    const data = JSON.parse(text);
                    if (data.schema_version !== 1 || !Array.isArray(data.providers))
                        throw new Error("Unsupported status schema");
                    root.providers = data.providers;
                    root.error = "";
                } catch (e) {
                    root.providers = [];
                    root.error = "Cannot read AIQuota cached status.";
                }
            }
        }
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0) {
                root.providers = [];
                root.error = "AIQuota is unavailable. Check that it is installed and on PATH.";
            }
        }
    }

    Column {
        id: contentColumn
        width: root.width
        spacing: Tokens.spacing.medium

        StyledText {
            text: "AI quota"
            font: Tokens.font.title.small
        }

        StyledText {
            visible: root.error.length > 0
            width: parent.width
            wrapMode: Text.Wrap
            text: root.error
            color: Colours.palette.m3onSurfaceVariant
        }

        Repeater {
            model: root.providers

            delegate: Column {
                id: section
                required property var modelData
                width: contentColumn.width
                spacing: Tokens.spacing.small

                Row {
                    width: parent.width
                    spacing: Tokens.spacing.small

                    StyledText {
                        text: section.modelData.name || section.modelData.id
                        font: Tokens.font.title.small
                    }
                    StyledText {
                        text: section.modelData.status || "unknown"
                        color: Colours.palette.m3onSurfaceVariant
                    }
                }

                StyledText {
                    visible: !!section.modelData.plan
                    text: section.modelData.plan || ""
                    color: Colours.palette.m3onSurfaceVariant
                }

                StyledText {
                    visible: !!section.modelData.credits
                    text: !section.modelData.credits ? "" : section.modelData.credits.unlimited ? "Credits: unlimited" : section.modelData.credits.balance != null ? "Credits: " + section.modelData.credits.balance : section.modelData.credits.has_credits === true ? "Credits available" : section.modelData.credits.has_credits === false ? "No credits available" : "Credits: unknown"
                    color: Colours.palette.m3onSurfaceVariant
                }

                StyledText {
                    visible: !!section.modelData.message
                    width: parent.width
                    wrapMode: Text.Wrap
                    text: section.modelData.message || ""
                    color: Colours.palette.m3onSurfaceVariant
                }

                StyledText {
                    visible: section.modelData.status !== "healthy" && !!section.modelData.last_success
                    text: "Last update " + new Date(section.modelData.last_success).toLocaleString()
                    color: Colours.palette.m3onSurfaceVariant
                }

                Repeater {
                    model: section.modelData.windows || []

                    delegate: Column {
                        id: windowColumn
                        required property var modelData
                        width: section.width
                        spacing: Tokens.spacing.extraSmall

                        Row {
                            width: parent.width
                            StyledText {
                                width: parent.width - remaining.width
                                elide: Text.ElideRight
                                text: (windowColumn.modelData.label || windowColumn.modelData.id) + (windowColumn.modelData.duration_minutes == null ? "" : " (" + windowColumn.modelData.duration_minutes + " min)")
                            }
                            StyledText {
                                id: remaining
                                text: windowColumn.modelData.remaining_percent == null ? "Unknown" : Math.round(windowColumn.modelData.remaining_percent) + "% left"
                            }
                        }
                        StyledText {
                            visible: !!windowColumn.modelData.model
                            text: windowColumn.modelData.model || ""
                            color: Colours.palette.m3onSurfaceVariant
                        }
                        StyledText {
                            visible: windowColumn.modelData.used_amount != null || windowColumn.modelData.allocation_limit != null
                            text: (windowColumn.modelData.used_amount == null ? "Unknown" : windowColumn.modelData.used_amount) + " / " + (windowColumn.modelData.allocation_limit == null ? "unknown" : windowColumn.modelData.allocation_limit) + (windowColumn.modelData.unit ? " " + windowColumn.modelData.unit : "")
                            color: Colours.palette.m3onSurfaceVariant
                        }
                        Rectangle {
                            width: parent.width
                            height: 5
                            radius: height / 2
                            color: Colours.palette.m3surfaceContainerHighest
                            visible: windowColumn.modelData.remaining_percent != null
                            Rectangle {
                                width: parent.width * Math.max(0, Math.min(100, windowColumn.modelData.remaining_percent || 0)) / 100
                                height: parent.height
                                radius: parent.radius
                                color: Colours.palette.m3primary
                            }
                        }
                        StyledText {
                            text: root.displayTime(windowColumn.modelData.resets_at)
                            color: Colours.palette.m3onSurfaceVariant
                        }
                    }
                }
            }
        }
    }
}
