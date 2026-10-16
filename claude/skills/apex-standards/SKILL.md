---
name: apex-standards
description: Verbindliche Apex-Standards des Hauses (Trigger-Framework, Sharing, Sicherheit, Fehlerbehandlung). Immer verwenden, wenn Apex-Klassen oder Trigger geschrieben, geändert oder reviewt werden – auch bei kleinen Änderungen.
---
# Apex-Standards

> Platzhalter in <> durch eure Hausstandards ersetzen.

## Trigger
- Genau ein Trigger pro Objekt: `<Objekt>Trigger`, enthält keine Logik.
- Logik in Handler-Klasse `<Objekt>TriggerHandler extends <EuerFramework>`.
- Rekursionsschutz über das Framework, nicht über statische Booleans in Einzelklassen.

## Klassenaufbau
- Service-Klassen (`<Fachbegriff>Service`) für Geschäftslogik, Selector-Klassen (`<Objekt>Selector`) für SOQL.
- Jede Klasse deklariert explizit `with sharing`, `without sharing` (nur mit Begründung im Design) oder `inherited sharing`.

## Sicherheit
- SOQL mit `WITH USER_MODE`, DML mit `Database.insert(records, AccessLevel.USER_MODE)` – außer in begründeten System-Kontexten.
- Keine dynamische SOQL mit String-Konkatenation von Benutzereingaben; Bind-Variablen oder `Database.queryWithBinds`.

## Limits
- Kein SOQL/DML in Schleifen. Immer für 200 Datensätze denken.
- Maps statt verschachtelter Schleifen für Zuordnungen.

## Fehlerbehandlung
- Keine leeren `catch`-Blöcke. Fehler loggen über <Logging-Framework, z. B. Nebula Logger>.
- Benutzerrelevante Fehler über `addError()` am Datensatz.
