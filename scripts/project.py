#!/usr/bin/env python3
"""
Liest die Projekt-Registry (projects.json) und prüft, ob ein Ticket in diesem Repo laufen darf.

  project.py env <TICKET> <REPO>   Prüft Projekt + Repo, gibt KEY=WERT-Zeilen für $GITHUB_ENV aus
  project.py list                  Tabelle aller Projekte (für /meine-tickets und Menschen)

Registry: Umgebungsvariable AGENT_KIT_REGISTRY, sonst projects.json neben diesem Skript.
"""
import json, os, re, sys

REGISTRY = os.environ.get("AGENT_KIT_REGISTRY") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "projects.json")


def load():
    with open(REGISTRY, encoding="utf-8") as fh:
        return json.load(fh)


def env(ticket, repo):
    if not re.fullmatch(r"[A-Z][A-Z0-9]+-[0-9]+", ticket):
        sys.exit(f"Ungültiges Ticket '{ticket}'.")
    reg = load()
    key = ticket.split("-")[0]
    project = reg["projects"].get(key)
    if not project:
        sys.exit(f"Projekt {key} steht nicht in projects.json – Lauf abgelehnt.")
    if project["repo"].casefold() != repo.casefold():
        sys.exit(f"Projekt {key} gehört zu {project['repo']}, nicht zu {repo} – Lauf abgelehnt.")
    if not project.get("approvers"):
        sys.exit(f"Für Projekt {key} sind keine Freigeber (approvers) hinterlegt.")
    status = {**reg["defaults"]["status"], **project.get("status", {})}
    out = {
        "PROJECT_KEY": key,
        "JIRA_BASE_URL": project.get("jira_base_url", reg["jira_base_url"]),
        "JIRA_APPROVERS": ",".join(project["approvers"]),
        "ST_ANALYSE": status["analyse"],
        "ST_DESIGN_REVIEW": status["design_review"],
        "ST_APPROVED": status["approved"],
        "ST_BUILD": status["build"],
        "ST_CODE_REVIEW": status["code_review"],
    }
    for k, v in out.items():
        if "\n" in v:
            sys.exit(f"Ungültiger Wert für {k}.")
        print(f"{k}={v}")


def list_projects():
    reg = load()
    print("| Projekt | Name | Repo | Lokaler Ordner |")
    print("|---|---|---|---|")
    for key, p in sorted(reg["projects"].items()):
        print(f"| {key} | {p.get('name', '')} | {p['repo']} | {p.get('local_path', '–')} |")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "env":
        env(sys.argv[2], sys.argv[3])
    elif len(sys.argv) == 2 and sys.argv[1] == "list":
        list_projects()
    else:
        sys.exit(__doc__)
