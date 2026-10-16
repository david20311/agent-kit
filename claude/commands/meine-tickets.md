---
description: Alle mir zugewiesenen Tickets über alle angebundenen Jira-Projekte – mit Repo und nächstem Schritt
argument-hint: [Projekt-Key, optional]
---
Zeige dem Menschen seine offenen Agent-Tickets über alle Projekte hinweg. Nur lesen – nichts in Jira ändern.

1. Lies `.claude/projects.json` (Registry). Relevante Projekte: alle Keys unter `projects`, bei Argument `$ARGUMENTS` nur dieses.
2. Suche über den Atlassian-Connector (`searchJiraIssuesUsingJql`, Site aus `jira_base_url`):
   `project in (<Keys>) AND assignee = currentUser() AND statusCategory != Done ORDER BY project, status, updated DESC`
   Felder: summary, status, reporter, updated.
3. Ausgabe als Tabelle, gruppiert nach Projekt (Name, Repo, lokaler Ordner aus der Registry):
   | Ticket | Titel | Status | Nächster Schritt |
   Nächster Schritt je Status (Namen aus `defaults.status` bzw. projektspezifisch):
   - Zu erledigen → automatisch: wartet auf Pipeline-Start / interaktiv: `/analysieren <TICKET>` im Projektordner
   - In Analyse → Agent läuft (Pipeline) oder Feedback wird eingearbeitet
   - Design-Review → **Mensch**: Design im Ticket prüfen, dann nach „Freigegeben“ oder mit Feedback zurück nach „In Analyse“
   - Freigegeben → automatisch: Umsetzung startet / interaktiv: `scripts/freigeben.sh <TICKET>` im Terminal, dann `/bauen <TICKET>`
   - In Umsetzung → Agent baut
   - Code-Review → **Mensch**: Pull Request prüfen und mergen
4. Liegt das aktuelle Arbeitsverzeichnis nicht im Repo eines aufgeführten Projekts, weise darauf hin,
   dass `/analysieren` und `/bauen` im jeweiligen Projektordner gestartet werden müssen (`local_path`).
5. Tickets aus Projekten, die nicht in der Registry stehen, nicht anzeigen – höchstens die Anzahl nennen.
