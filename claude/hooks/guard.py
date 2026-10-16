#!/usr/bin/env python3
"""
Harte Leitplanken für alle Agents, unabhängig vom Prompt.

Wird von Claude Code vor jedem Bash-, Write- und Edit-Aufruf ausgeführt.
Exit-Code 2 blockiert den Aufruf; die Meldung auf stderr sieht Claude.
Jede Entscheidung wird in .claude/hooks/audit.log protokolliert.
"""
import json, os, re, shlex, sys, datetime

# Orgs, die Agents überhaupt ansprechen dürfen
ALLOWED_ORGS = {"agent-dev", "agent-int"}
# Orgs, auf die nur validiert (nicht deployed) werden darf
VALIDATE_ONLY_ORGS = {"agent-int"}
# Atlassian-Connector (MCP): nur diese Werkzeuge sind erlaubt, alles andere wird blockiert
ATLASSIAN_ALLOWED = {
    "getAccessibleAtlassianResources", "atlassianUserInfo", "getJiraIssue", "searchJiraIssuesUsingJql",
    "getTransitionsForJiraIssue", "getVisibleJiraProjects", "lookupJiraAccountId", "getJiraIssueRemoteIssueLinks",
    "getConfluencePage", "searchConfluenceUsingCql", "search", "fetch",
    "addCommentToJiraIssue", "transitionJiraIssue",
}
# sf-Befehle, die eine Org berühren und deshalb --target-org erfordern
ORG_COMMANDS = ("project deploy", "project retrieve", "data ", "apex ", "sobject ", "org open", "org display")

PROJECT_DIR = os.environ.get("CLAUDE_PROJECT_DIR", ".")
LOG = os.path.join(PROJECT_DIR, ".claude", "hooks", "audit.log")


def log(decision, tool, detail):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            ts = datetime.datetime.now().isoformat(timespec="seconds")
            f.write(f"{ts}\t{decision}\t{tool}\t{detail[:300]}\n")
    except OSError:
        pass


def block(tool, detail, reason):
    log("BLOCK", tool, detail)
    print(f"Blockiert durch guard.py: {reason}", file=sys.stderr)
    sys.exit(2)


def target_orgs(tokens):
    orgs = []
    for i, t in enumerate(tokens):
        if t in ("--target-org", "-o") and i + 1 < len(tokens):
            orgs.append(tokens[i + 1])
        elif t.startswith("--target-org="):
            orgs.append(t.split("=", 1)[1])
    return orgs


def check_sf_segment(segment, full):
    try:
        tokens = shlex.split(segment)
    except ValueError:
        tokens = segment.split()
    if not tokens or tokens[0] not in ("sf", "sfdx"):
        return
    if tokens[0] == "sfdx":
        block("Bash", full, "Bitte die aktuelle `sf`-CLI verwenden, nicht `sfdx`.")

    sub = " ".join(tokens[1:3]) + " "
    orgs = target_orgs(tokens)

    if any(sub.startswith(c) for c in ORG_COMMANDS):
        if not orgs:
            block("Bash", full, "sf-Befehle gegen eine Org brauchen immer ein explizites --target-org.")
        for org in orgs:
            if org not in ALLOWED_ORGS:
                block("Bash", full, f"Org '{org}' ist für Agents nicht freigegeben. Erlaubt: {sorted(ALLOWED_ORGS)}")

    if sub.startswith("project deploy"):
        is_validate = "validate" in tokens[1:4] or "--dry-run" in tokens
        for org in orgs:
            if org in VALIDATE_ONLY_ORGS and not is_validate:
                block("Bash", full, f"Auf '{org}' ist nur `sf project deploy validate` erlaubt.")


def check_bash(cmd):
    # Befehlsketten (&&, ;, |) einzeln prüfen
    for segment in re.split(r"&&|\|\||;|\|", cmd):
        check_sf_segment(segment.strip(), cmd)
    if re.search(r"freigeben\.sh", cmd):
        block("Bash", cmd, "Die Freigabe (scripts/freigeben.sh) führt ausschließlich ein Mensch aus.")
    if re.search(r"agent-kit/install\.sh|(^|[\s;&|])\./install\.sh", cmd):
        block("Bash", cmd, "install.sh ersetzt die Leitplanken der Agents und läuft nur durch einen Menschen.")
    if re.search(r"\bgit\s+push\b", cmd):
        block("Bash", cmd, "git push macht die Pipeline bzw. ein Mensch, nicht der Agent.")


def check_write(tool_input):
    path = tool_input.get("file_path", "")
    text = "\n".join(str(tool_input.get(k, "")) for k in ("content", "new_string"))
    for edit in tool_input.get("edits", []) or []:
        text += "\n" + str(edit.get("new_string", ""))
    # Gate 1 schützen: Freigabe setzt nur ein Mensch
    if "docs/design/" in path and re.search(r"^\s*Status:\s*Freigegeben", text, re.M | re.I):
        block("Write", path, "Die Freigabe eines Designs (Status: Freigegeben) setzt ausschließlich ein Mensch.")
    if re.search(r"(^|/)\.claude/(settings\.json|hooks/)", path):
        block("Write", path, "Agents dürfen ihre eigenen Leitplanken nicht ändern.")


def check_atlassian(tool, tool_input):
    name = tool.rsplit("__", 1)[-1]
    detail = f"{name} {tool_input.get('issueIdOrKey', '')}"
    if name not in ATLASSIAN_ALLOWED:
        block(tool, detail, f"Jira/Confluence-Werkzeug '{name}' ist für Agents nicht freigegeben (nur lesen, kommentieren, Status).")
    if name == "addCommentToJiraIssue" and tool_input.get("commentId"):
        block(tool, detail, "Bestehende Kommentare dürfen nicht geändert werden – nur neue Kommentare.")
    if name == "transitionJiraIssue" and (tool_input.get("fields") or tool_input.get("update")):
        block(tool, detail, "Beim Statuswechsel dürfen keine Felder geändert werden.")
    log("ALLOW", tool, detail)


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Fail closed: lieber einen Aufruf zu viel blockieren als einen zu wenig
        print("Blockiert durch guard.py: Hook-Eingabe nicht lesbar.", file=sys.stderr)
        sys.exit(2)
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    if tool == "Bash":
        cmd = tool_input.get("command", "")
        check_bash(cmd)
        log("ALLOW", tool, cmd)
    elif tool in ("Write", "Edit", "MultiEdit"):
        check_write(tool_input)
        log("ALLOW", tool, tool_input.get("file_path", ""))
    elif tool.startswith("mcp__") and "tlassian" in tool:
        check_atlassian(tool, tool_input)
    sys.exit(0)


if __name__ == "__main__":
    main()
