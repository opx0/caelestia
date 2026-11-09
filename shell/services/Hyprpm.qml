pragma Singleton
pragma ComponentBehavior: Bound

import QtQuick
import Quickshell
import Quickshell.Io
import Caelestia.I18n

Singleton {
    id: root

    property bool available: true
    property bool loaded: false
    property bool loading: false
    property bool busy: false
    property bool refreshPending: false
    property string lastError: ""
    property list<var> plugins: []

    readonly property int installedCount: plugins.length
    readonly property int enabledCount: plugins.filter(p => p.enabled).length
    readonly property int failedCount: plugins.filter(p => p.failed).length

    function refresh(): void {
        if (listProc.running) {
            refreshPending = true;
            return;
        }

        loading = true;
        listProc.running = true;
    }

    function setEnabled(plugin: var, enabled: bool): void {
        if (busy || !plugin || plugin.failed || plugin.enabled === enabled)
            return;

        busy = true;
        lastError = "";
        mutateProc.command = ["hyprpm", enabled ? "enable" : "disable", plugin.identifier];
        mutateProc.running = true;
    }

    function reload(): void {
        if (busy)
            return;

        busy = true;
        lastError = "";
        reloadProc.running = true;
    }

    function cleanOutput(text: string): string {
        return text.replace(/\x1b\[[0-9;]*m/g, "").trim();
    }

    function parseList(output: string): list<var> {
        const result = [];
        let repository = "";
        let author = "";
        let current = null;

        for (const rawLine of root.cleanOutput(output).split("\n")) {
            const line = rawLine.trim();
            const repoMatch = line.match(/Repository (.+) \(by (.+)\):/);
            if (repoMatch) {
                repository = repoMatch[1].trim();
                author = repoMatch[2].trim();
                current = null;
                continue;
            }

            const nameMatch = line.match(/^[│|]\s*Plugin\s+(.+)$/);
            if (nameMatch) {
                const name = nameMatch[1].trim();
                current = {
                    name: name,
                    repository: repository,
                    author: author,
                    identifier: author ? `${author}/${name}` : name,
                    enabled: false,
                    failed: false
                };
                result.push(current);
                continue;
            }

            const stateMatch = line.match(/^[└┗]\S*\s*enabled: (.*)$/);
            if (!stateMatch || !current)
                continue;

            const state = stateMatch[1].trim();
            current.enabled = state === "true";
            current.failed = state !== "true" && state !== "false";
        }

        return result;
    }

    Component.onCompleted: refresh()

    Process {
        id: listProc

        command: ["sh", "-c", "hyprpm list 2>/dev/null"]

        stdout: StdioCollector {
            id: listOut
        }

        onExited: code => { // qmllint disable signal-handler-parameters
            root.loading = false;
            root.loaded = true;
            root.available = code !== 127;

            if (root.available) {
                root.plugins = root.parseList(listOut.text ?? "");
                if (code !== 0 && root.lastError.length === 0)
                    root.lastError = Tr.tr("Could not read HyprPM plugin state");
            } else {
                root.plugins = [];
            }

            if (root.refreshPending) {
                root.refreshPending = false;
                root.refresh();
            }
        }
    }

    Process {
        id: mutateProc

        stderr: StdioCollector {
            id: mutateErr
        }

        onExited: code => { // qmllint disable signal-handler-parameters
            if (code !== 0) {
                const error = root.cleanOutput(mutateErr.text ?? "");
                root.lastError = error.length > 0 ? error : Tr.tr("Failed to change the plugin state");
                root.busy = false;
                root.refresh();
                return;
            }

            reloadProc.running = true;
        }
    }

    Process {
        id: reloadProc

        stderr: StdioCollector {
            id: reloadErr
        }

        onExited: code => { // qmllint disable signal-handler-parameters
            if (code !== 0) {
                const error = root.cleanOutput(reloadErr.text ?? "");
                root.lastError = error.length > 0 ? error : Tr.tr("Failed to reload plugins");
            }

            root.busy = false;
            root.refresh();
        }
    }
}
