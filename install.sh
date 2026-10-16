#!/usr/bin/env bash
# Spielt das agent-kit in ein Projekt-Repo ein oder aktualisiert es.
#
#   ./install.sh <pfad-zum-projekt-repo>
#
# Kopiert (überschreibt) nur kit-verwaltete Dateien:
#   claude/**            -> <projekt>/.claude/**   (Agents, Skills, Befehle, Hook, settings.json)
#   projects.json        -> <projekt>/.claude/projects.json
#   scripts/freigeben.sh -> <projekt>/scripts/freigeben.sh
#   templates/*.yml      -> <projekt>/.github/workflows/  (nur wenn dort noch nicht vorhanden)
# Projektspezifisches bleibt unberührt: CLAUDE.md, force-app/, docs/, eigene Skills (z. B. .claude/skills/projekt-*).
#
# Weil dabei auch Hook und settings.json (die Leitplanken der Agents) ersetzt werden,
# läuft das Skript nur für Menschen im Terminal – nicht aus Claude Code heraus.
set -euo pipefail

if [ -n "${CLAUDECODE:-}" ] || [ ! -t 0 ]; then
  echo "install.sh ändert die Leitplanken der Agents und läuft nur für Menschen im Terminal." >&2
  exit 2
fi

KIT="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-}"
[ -n "$TARGET" ] && [ -d "$TARGET/.git" ] || { echo "Aufruf: ./install.sh <pfad-zum-projekt-repo> (Git-Repo)" >&2; exit 1; }
TARGET="$(cd "$TARGET" && pwd)"
[ -f "$TARGET/sfdx-project.json" ] || { echo "$TARGET ist kein SFDX-Projekt (sfdx-project.json fehlt)." >&2; exit 1; }

VERSION="$(git -C "$KIT" describe --tags --always --dirty 2>/dev/null || echo unbekannt)"
echo "agent-kit $VERSION -> $TARGET"
read -r -p "Kit-Dateien im Projekt überschreiben? [j/N] " ANSWER
[[ "$ANSWER" =~ ^[jJyY]$ ]] || { echo "Abgebrochen."; exit 1; }

mkdir -p "$TARGET/.claude" "$TARGET/scripts" "$TARGET/.github/workflows"
(cd "$KIT/claude" && find . -type f ! -name audit.log ! -name '*.pyc' -print0) | while IFS= read -r -d '' f; do
  mkdir -p "$TARGET/.claude/$(dirname "$f")"
  cp "$KIT/claude/$f" "$TARGET/.claude/$f"
done
cp "$KIT/projects.json" "$TARGET/.claude/projects.json"
cp "$KIT/scripts/freigeben.sh" "$TARGET/scripts/freigeben.sh"
chmod +x "$TARGET/scripts/freigeben.sh"
for wf in agent-run pr-validate; do
  if [ -f "$TARGET/.github/workflows/$wf.yml" ] && grep -q "agent-kit/.github/workflows/$wf.yml" "$TARGET/.github/workflows/$wf.yml"; then
    continue
  fi
  if [ -f "$TARGET/.github/workflows/$wf.yml" ]; then
    echo "Ersetze eigenständiges $wf.yml durch den Aufruf des agent-kit (alte Fassung: $wf.yml.vor-agent-kit)."
    mv "$TARGET/.github/workflows/$wf.yml" "$TARGET/.github/workflows/$wf.yml.vor-agent-kit"
  fi
  cp "$KIT/templates/project-$wf.yml" "$TARGET/.github/workflows/$wf.yml"
done
echo "$VERSION" > "$TARGET/.claude/agent-kit.version"

echo
git -C "$TARGET" status --short
echo
echo "✅ Fertig. Änderungen prüfen (git diff) und committen. Claude Code im Projekt neu starten, damit der Hook neu geladen wird."
