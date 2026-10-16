#!/usr/bin/env bash
# Gate 1: Ein Mensch gibt das Solution Design frei.
# Setzt in docs/design/<TICKET>.md die Zeile "Status: Freigegeben (<Name>, <Datum>)" und committet.
# Nur für Menschen im Terminal – Aufrufe aus Claude Code oder ohne interaktive Eingabe werden abgelehnt.
#
#   scripts/freigeben.sh CT-123
set -euo pipefail

TICKET="${1:-}"
[[ "$TICKET" =~ ^[A-Z][A-Z0-9]+-[0-9]+$ ]] || { echo "Aufruf: scripts/freigeben.sh <TICKET>, z. B. CT-123" >&2; exit 1; }

if [ -n "${CLAUDECODE:-}" ] || [ ! -t 0 ]; then
  echo "Die Freigabe setzt ausschließlich ein Mensch – bitte selbst im Terminal ausführen." >&2
  exit 2
fi

cd "$(git rev-parse --show-toplevel)"
BRANCH="feature/$TICKET"
DESIGN="docs/design/$TICKET.md"

[ "$(git branch --show-current)" = "$BRANCH" ] || git checkout "$BRANCH"
[ -f "$DESIGN" ] || { echo "$DESIGN fehlt – erst /analysieren $TICKET." >&2; exit 1; }
if grep -q "^Status: Freigegeben" "$DESIGN"; then
  echo "$TICKET ist bereits freigegeben: $(grep -m1 '^Status:' "$DESIGN")"
  exit 0
fi

NAME="$(git config user.name || true)"
[ -n "$NAME" ] || { echo "git config user.name ist nicht gesetzt." >&2; exit 1; }

echo "Design:  $DESIGN"
echo "Aktuell: $(grep -m1 '^Status:' "$DESIGN" || echo '(keine Statuszeile)')"
read -r -p "Hast du das Design gelesen und gibst es als $NAME frei? [j/N] " ANSWER
[[ "$ANSWER" =~ ^[jJyY]$ ]] || { echo "Abgebrochen."; exit 1; }

APPROVAL="Status: Freigegeben ($NAME, $(date +%F))" python3 -I - "$DESIGN" <<'PY'
import os, re, sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
text, n = re.subn(r"^Status:.*$", os.environ["APPROVAL"], text, count=1, flags=re.M)
if not n:
    sys.exit("Keine Statuszeile im Design-Dokument gefunden.")
open(path, "w", encoding="utf-8").write(text)
PY

git add "$DESIGN"
git commit -q -m "$TICKET: Design freigegeben durch $NAME"
echo "✅ $TICKET freigegeben. Nächste Schritte: Ticket in Jira nach „Freigegeben“ verschieben, dann /bauen $TICKET."
