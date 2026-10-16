---
name: flow-standards
description: Verbindliche Regeln für Salesforce Flows (Benennung, Before/After-Save, Fehlerpfade, Dokumentation). Immer verwenden, wenn Flows erstellt, geändert oder reviewt werden.
---
# Flow-Standards

- Benennung: `<Objekt>_<Zeitpunkt>_<Zweck>`, z. B. `Opportunity_BeforeSave_SetDiscount`.
- Feldaktualisierungen am auslösenden Datensatz: Before-Save-Flow (Fast Field Update), nicht After-Save.
- Pro Objekt und Zeitpunkt möglichst ein Flow mit Entscheidungen statt vieler kleiner Flows; Trigger Order setzen, wenn mehrere existieren.
- Einstiegsbedingungen immer gesetzt, damit der Flow nicht bei jeder Änderung läuft.
- Keine Get/Update-Elemente in Schleifen.
- Jedes DML-Element hat einen Fault-Pfad mit Fehlerbehandlung <z. B. Subflow Error_Log>.
- Jedes Element hat eine Beschreibung; der Flow selbst verweist im Beschreibungsfeld auf das Ticket.
- Hardcodierte IDs sind verboten; Custom Metadata oder Custom Labels verwenden.
