---
name: naming-conventions
description: Namenskonventionen für alle Salesforce-Metadaten (Objekte, Felder, Klassen, Permission Sets, LWC). Immer verwenden, wenn neue Metadaten angelegt oder benannt werden.
---
# Namenskonventionen

| Metadatum | Muster | Beispiel |
|---|---|---|
| Custom Object | `<Fachbegriff>__c`, Englisch, Singular | `Contract_Line__c` |
| Custom Field | `<Fachbegriff>__c`, mit Unterstrichen | `Discount_Rate__c` |
| Apex-Klasse | PascalCase + Rolle | `OpportunityService`, `AccountSelector` |
| Testklasse | `<Klasse>Test` | `OpportunityServiceTest` |
| Permission Set | `<Bereich>_<Rolle>` | `Sales_Discount_Manager` |
| LWC | camelCase | `discountCalculator` |
| Custom Metadata | `<Zweck>_Setting__mdt` | `Discount_Setting__mdt` |

- Jedes neue Feld und Objekt hat eine Beschreibung und, wo sinnvoll, einen Hilfetext.
- <Präfix-Regel, falls ihr eines verwendet>
