---
name: test-standards
description: Regeln für Apex-Testklassen (Testdaten, Abdeckung, Assertions, Bulk- und Berechtigungstests). Immer verwenden, wenn Tests geschrieben, ergänzt oder reviewt werden.
---
# Test-Standards

- Testdaten über eine zentrale Factory: <z. B. TestDataFactory>. Keine `SeeAllData=true`.
- `@TestSetup` für gemeinsame Daten.
- Jeder Test hat mindestens eine aussagekräftige Assertion mit Meldung: `Assert.areEqual(erwartet, ist, 'Grund')`.
- Pflichtfälle je Funktion: positiv, negativ, Bulk (200 Datensätze), eingeschränkter User via `System.runAs`.
- `Test.startTest()` / `Test.stopTest()` um den eigentlichen Aufruf.
- Coverage-Ziel: 85 % je geänderter Klasse (Salesforce-Minimum 75 % ist nicht das Ziel).
- Callouts nur über `HttpCalloutMock`.
