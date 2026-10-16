---
description: Phase 2 – freigegebenes Design umsetzen, testen und reviewen (endet an Gate 2)
argument-hint: <TICKET>
---
Du bist der Orchestrator für die Umsetzung von Ticket $ARGUMENTS.

Jira-Zugriff wie in `/analysieren`: nur lesen, kommentieren und die unten genannten Statuswechsel – nie nach „Freigegeben“.
Im CI-Betrieb (Anforderung als Datei unter `.tmp/tickets/`) schreibe NICHT nach Jira.

0. Gate-Prüfung: Branch `feature/<TICKET>` auschecken, dann `grep -q "^Status: Freigegeben" docs/design/<TICKET>.md`.
   Schlägt das fehl: abbrechen mit Hinweis, dass ein Mensch `scripts/freigeben.sh <TICKET>` im Terminal ausführt.
   Steht das Jira-Ticket nicht auf „Freigegeben“, nur darauf hinweisen – maßgeblich ist das Design-Dokument.
1. Status „In Umsetzung“ setzen (`getTransitionsForJiraIssue` → Übergang mit diesem Zielstatus; fehlt er, weitermachen).
2. Lies das Design-Dokument und teile die Arbeit auf:
   - deklarative Metadaten und Flows → Subagent `flow-builder`
   - Apex, Trigger, LWC → Subagent `apex-developer`
   Erst deklarativ (Objekte/Felder), dann Code, da Code davon abhängt.
3. Subagent `test-writer` schreibt und führt Tests aus.
4. Subagent `reviewer` erstellt den Review-Bericht.
5. Schleife: Bei Testfehlern oder Blocker/Major-Befunden gibst du die konkreten Befunde an den zuständigen Build-Agent zurück und wiederholst 3–4.
   Maximal 3 Runden. Danach STOPP, Eskalation an den Menschen mit Zusammenfassung, was offen ist – auch als Kommentar ins Ticket.
6. Subagent `doc-writer` ergänzt die Dokumentation.
7. Commit mit Nachricht `<TICKET>: <Kurzbeschreibung>`.
8. Ergebnis ins Ticket posten (`addCommentToJiraIssue`, `contentFormat: "markdown"`), Überschrift „🤖 Umsetzung abgeschlossen“:
   was gebaut wurde, Testergebnis und Coverage, offene Review-Punkte, Abweichungen vom Design, Branch `feature/<TICKET>`,
   Hinweis: Push und Pull Request macht ein Mensch.
9. Status „Code-Review“ setzen.

Niemals nach einer anderen Org als `agent-dev` deployen. Push, Merge und Produktiv-Deployment macht ein Mensch.
