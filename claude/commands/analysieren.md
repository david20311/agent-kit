---
description: Phase 1 – Anforderung analysieren und Design-Dokument erstellen (endet an Gate 1)
argument-hint: <TICKET> [Anforderungstext, falls kein Jira-Zugriff]
---
Du bist der Orchestrator für die Umsetzung von Ticket $ARGUMENTS.

Jira-Zugriff (interaktiver Betrieb): über den Atlassian-Connector (MCP), Site `techrockets.atlassian.net`.
Erlaubt sind nur: Ticket lesen, Kommentar hinzufügen, Statuswechsel nach den unten genannten Status.
Verschiebe ein Ticket NIEMALS nach „Freigegeben“ und ändere keine Felder, Bearbeiter oder fremden Kommentare.
Liegt die Anforderung stattdessen als Datei vor (CI-Betrieb, z. B. `.tmp/tickets/<TICKET>.md`), schreibe NICHT nach Jira – das macht die Pipeline.

1. Anforderung beschaffen: Lies das Jira-Ticket inkl. Kommentaren (`getJiraIssue` mit `fields: ["*all", "comment"]`, Format Markdown). Ohne Jira-Zugriff nutze den mitgegebenen Text.
   Fehlen Akzeptanzkriterien oder sind sie widersprüchlich: Liste die Lücken, poste sie als Kommentar ins Ticket
   (Überschrift „🤖 Rückfragen vor dem Design“) und STOPPE.
2. Status „In Analyse“ setzen: Übergänge mit `getTransitionsForJiraIssue` holen, den mit Zielstatus „In Analyse“ ausführen. Gibt es ihn nicht, weitermachen und am Ende erwähnen.
3. Branch anlegen: `git checkout -b feature/<TICKET>` (falls nicht vorhanden, sonst auschecken).
4. Bestimme die betroffenen Objekte und beauftrage den Subagent `org-discovery` damit.
5. Beauftrage den Subagent `architect` mit Anforderung + Org-Kontext.
   Existiert `docs/design/<TICKET>.md` bereits, gib ihm die Kommentare seit dem letzten Design-Kommentar als Feedback mit: überarbeiten statt neu schreiben.
6. Committe Design und Org-Kontext auf dem Branch: `<TICKET>: Solution Design (Entwurf)`.
7. Design ins Ticket posten (`addCommentToJiraIssue`, `contentFormat: "markdown"`, immer einen NEUEN Kommentar):
   ```
   🤖 Solution Design (Entwurf) – bitte prüfen

   - Passt es: Freigabe im Terminal mit `scripts/freigeben.sh <TICKET>`, danach Ticket nach „Freigegeben“ verschieben und `/bauen <TICKET>` starten.
   - Änderungswünsche: als Kommentar ins Ticket schreiben und `/analysieren <TICKET>` erneut starten.

   Branch: feature/<TICKET>
   ---
   <vollständiger Inhalt von docs/design/<TICKET>.md>
   ```
   Bei einer Überarbeitung zuerst kurz die Änderungen gegenüber der letzten Fassung auflisten.
8. Status „Design-Review“ setzen (wie Schritt 2).
9. Fasse für den Menschen zusammen: Kernentscheidungen des Designs, Risiken, offene Fragen, Link zum Ticket.

ENDE der Phase. Baue NICHTS. Die Freigabe (`Status: Freigegeben` im Design-Dokument) setzt ausschließlich ein Mensch.
