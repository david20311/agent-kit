# agent-kit

Gemeinsame Basis für Claude-Agents über mehrere Jira-Projekte hinweg. Jedes Jira-Projekt (Board) hat sein
eigenes Repo mit eigenem Kundenkontext und eigenen Zugängen; Agents, Regeln und Pipeline liegen einmal hier.

```
            Jira-Site (alle Boards)
   CT ─┐   ABC ─┐   XYZ ─┐
       └────────┴────────┴──► eine globale Automation-Regel
                              Nachschlagetabelle Projekt → Repo
                                        │ repository_dispatch
             ┌──────────────────────────┼──────────────────────────┐
             ▼                          ▼                          ▼
      Projekt-Repo CT             Projekt-Repo ABC           Projekt-Repo XYZ
      CLAUDE.md, force-app,       …                          …
      eigene Secrets
      .github/workflows/agent-run.yml ──uses──► agent-kit/.github/workflows/agent-run.yml
```

## Inhalt

| Pfad | Zweck |
|---|---|
| `claude/` | Agents, Skills, Befehle, Hook, settings.json – wird per `install.sh` nach `<projekt>/.claude/` kopiert |
| `claude/commands/meine-tickets.md` | `/meine-tickets`: alle zugewiesenen Tickets über alle Projekte |
| `projects.json` | **Registry/Positivliste**: Jira-Projekt → Repo, Freigeber, Statusnamen |
| `scripts/project.py` | liest und prüft die Registry (Pipeline und Menschen) |
| `scripts/jira.py` | Jira-Anbindung der Pipeline (Kommentare, Status, Gate 1) |
| `scripts/freigeben.sh` | Gate 1 im interaktiven Betrieb (nur Menschen) |
| `.github/workflows/agent-run.yml` | zentraler Agent-Lauf (reusable workflow) |
| `.github/workflows/pr-validate.yml` | zentrale PR-Prüfung, Gate 2 (reusable workflow) |
| `templates/` | dünne Workflows für Projekt-Repos |
| `install.sh` | Kit in ein Projekt-Repo einspielen/aktualisieren (nur Menschen) |

## Sicherheitsprinzipien

- **Trennung pro Projekt:** Sandbox-Zugang und Jira-Token liegen als Secrets im jeweiligen Projekt-Repo.
  Ein Lauf für Projekt A kann die Org von Projekt B nicht erreichen.
- **Positivliste:** Die Pipeline bricht ab, wenn das Jira-Projekt des Tickets nicht in `projects.json`
  steht oder einem anderen Repo zugeordnet ist.
- **Gate 1:** Nur Personen aus `approvers` des Projekts können per Jira-Statuswechsel freigeben.
- **Leitplanken:** Hook und settings.json kommen aus dem Kit; Agents können sie nicht ändern, und
  `install.sh`/`freigeben.sh` laufen nur für Menschen.

## Neues Projekt anbinden

1. **Repo** anlegen (SFDX-Projekt) mit eigener `CLAUDE.md` (Kunde, Clouds, Konventionen, No-Gos).
2. **Kit einspielen:** `./install.sh <pfad-zum-projekt-repo>` → Änderungen prüfen, committen, hochladen.
3. **Registry:** Eintrag in `projects.json` ergänzen (Key, Repo, `local_path`, `approvers`), committen, hochladen.
4. **Secrets im Projekt-Repo:** `ANTHROPIC_API_KEY`, `SF_AUTH_URL_AGENT_DEV`, `SF_AUTH_URL_AGENT_INT`,
   `JIRA_USER`, `JIRA_API_TOKEN`, bei privatem Kit zusätzlich `AGENT_KIT_TOKEN`.
   *Settings → Actions → General*: „Read and write permissions“ + „Allow GitHub Actions to create … pull requests“.
5. **Jira-Board:** Status wie unten anlegen (gleiche Namen in allen Boards).
6. **Jira-Regel:** Projekt in die Nachschlagetabelle der globalen Regel aufnehmen und das Projekt zum
   Geltungsbereich der Regel hinzufügen.

Status je Board: Zu erledigen → In Analyse → Design-Review → Freigegeben (nur Mensch) → In Umsetzung → Code-Review → Erledigt.
Abweichende Namen pro Projekt in `projects.json` unter `"status"` überschreiben.

## Globale Jira-Automation (einmal für alle Projekte)

*Jira-Einstellungen → System → Globale Automatisierung* (Jira-Admin nötig) → Regel erstellen,
Geltungsbereich: **mehrere Projekte** (alle angebundenen).

Am Anfang jeder Regel: Aktion **„Nachschlagetabelle erstellen“**, Name `repos`:

| Schlüssel | Wert |
|---|---|
| `CT` | `david20311/claude-jira-bot` |
| `ABC` | `<owner>/<repo>` |

Danach Aktion **Webanfrage senden**:
- URL: `https://api.github.com/repos/{{repos.get(issue.project.key)}}/dispatches`
- Methode `POST`, Header `Authorization: Bearer <GITHUB_TOKEN>` (versteckt), `Accept: application/vnd.github+json`,
  `X-GitHub-Api-Version: 2022-11-28`
- Body: `{"event_type":"agent-run","client_payload":{"ticket":"{{issue.key}}","phase":"<PHASE>"}}`

| Regel | Auslöser | Bedingungen | PHASE |
|---|---|---|---|
| 1 – Analyse | Vorgang zugewiesen | Bearbeiter = Agent-User **und** Status = Zu erledigen **und** `{{repos.get(issue.project.key)}}` ist nicht leer | `analysieren` |
| 2 – Überarbeitung | Vorgang übergegangen: von Design-Review nach In Analyse | Nachschlagewert nicht leer | `analysieren` |
| 3 – Umsetzung | Vorgang übergegangen: nach Freigegeben | Nachschlagewert nicht leer | `bauen` |

`<GITHUB_TOKEN>`: Fine-grained Token mit Zugriff auf **alle** Projekt-Repos, Berechtigung *Contents: Read and write*.

## Interaktiver Betrieb

Im Projektordner Claude Code starten: `/meine-tickets` zeigt alle zugewiesenen Tickets über alle Projekte
mit nächstem Schritt; `/analysieren` und `/bauen` laufen im jeweiligen Projektordner.

## Versionierung

Projekte rufen den Workflow mit `@main` auf (Demo). Für den echten Betrieb Releases taggen (`v1`, `v1.1`)
und in den Projekt-Workflows `@v1` verwenden, damit Änderungen am Kit bewusst übernommen werden.
