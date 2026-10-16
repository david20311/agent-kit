---
name: design-doc
description: Vorlage und Regeln für technische Design-Dokumente zu Salesforce-Anforderungen. Immer verwenden, wenn ein Design-Dokument erstellt oder geprüft wird.
---
# Design-Dokument

Datei: `docs/design/<TICKET>.md`. Exakt diese Struktur verwenden:

```markdown
# <TICKET>: <Titel>
Status: Entwurf
Freigegeben von: –
Datum: <JJJJ-MM-TT>

## Anforderung
<Zusammenfassung in eigenen Worten, 3–5 Sätze>

## Akzeptanzkriterien
AK1: ...
AK2: ...

## Lösungsansatz
<Deklarativ/programmatisch mit Begründung>

## Auswirkungen auf bestehende Org
<Konflikte laut Org-Kontext und deren Lösung>

## Zu ändernde Metadaten
| Typ | API-Name | Neu/Geändert | Zweck |

## Sicherheit und Berechtigungen
## Limits und Datenvolumen
## Testkonzept
| AK | Testklasse.Methode | Art (positiv/negativ/bulk/runAs) |

## Offene Fragen
## Risiken
```

Die Zeile `Status:` ändert nur ein Mensch auf `Freigegeben` (Gate 1).
