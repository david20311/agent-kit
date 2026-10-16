#!/usr/bin/env python3
"""
Jira-Anbindung für die Pipeline (nicht für Agents).

Der Agent selbst schreibt nie nach Jira. Kommentare, Statuswechsel und das Auslesen
der Freigabe erledigt ausschließlich der Workflow `agent-run.yml` mit diesem Skript.

Umgebung: JIRA_BASE_URL, JIRA_USER, JIRA_API_TOKEN (technischer User „Claude Agent“).

  jira.py fetch      <KEY> <AUSGABE.md>      Ticket inkl. Kommentaren als Markdown ablegen
  jira.py comment    <KEY> <DATEI.md> [--mention-reporter]
                                             Datei als Kommentar posten (Markdown → Jira-Wiki via pandoc),
                                             optional mit @Erwähnung des Erstellers (Jira benachrichtigt ihn)
  jira.py attach     <KEY> <DATEI>           Datei anhängen
  jira.py transition <KEY> <ZIELSTATUS>      Übergang in den Status mit diesem Namen auslösen
  jira.py assign-reporter <KEY>              Ticket an den Ersteller zurückgeben
  jira.py approval   <KEY> <FREIGABESTATUS>  Freigabe prüfen, gibt approver=/approver_id=/approved_at= aus
"""
import base64, json, mimetypes, os, shutil, subprocess, sys, urllib.error, urllib.request, uuid

BASE = os.environ.get("JIRA_BASE_URL", "").rstrip("/")
AUTH = base64.b64encode(f"{os.environ.get('JIRA_USER', '')}:{os.environ.get('JIRA_API_TOKEN', '')}".encode()).decode()
COMMENT_LIMIT = 30000  # Jira erlaubt max. 32.767 Zeichen pro Kommentar


def api(method, path, body=None, headers=None, raw=None):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    req.add_header("Authorization", f"Basic {AUTH}")
    req.add_header("Accept", "application/json")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode()
            return json.loads(text) if text else None
    except urllib.error.HTTPError as e:
        sys.exit(f"Jira {method} {path} -> HTTP {e.code}: {e.read().decode()[:500]}")


def fetch(key, out):
    issue = api("GET", f"/rest/api/3/issue/{key}?fields=summary,issuetype,status,reporter,labels,description,comment&expand=renderedFields")
    f, r = issue["fields"], issue.get("renderedFields") or {}
    lines = [
        f"# {key}: {f['summary']}",
        "",
        f"- Typ: {f['issuetype']['name']}",
        f"- Status: {f['status']['name']}",
        f"- Ersteller: {(f.get('reporter') or {}).get('displayName', '-')}",
        f"- Labels: {', '.join(f.get('labels') or []) or '-'}",
        "",
        "## Beschreibung (HTML aus Jira)",
        "",
        r.get("description") or "_keine Beschreibung_",
        "",
        "## Kommentare (älteste zuerst)",
        "",
    ]
    for c in (r.get("comment") or {}).get("comments", []):
        lines += [f"### {c['author']['displayName']} – {c['created']}", "", c.get("body", ""), ""]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def to_wiki(md_text):
    if not shutil.which("pandoc"):
        return md_text
    return subprocess.run(["pandoc", "-f", "gfm", "-t", "jira"], input=md_text,
                          capture_output=True, text=True, check=True).stdout


def reporter(key):
    return api("GET", f"/rest/api/3/issue/{key}?fields=reporter")["fields"].get("reporter")


def comment(key, path, *flags):
    with open(path, encoding="utf-8") as fh:
        text = to_wiki(fh.read())
    if len(text) > COMMENT_LIMIT:
        text = text[:COMMENT_LIMIT] + "\n\n_(gekürzt – vollständiges Dokument im Anhang)_"
    # Erwähnung erst nach der Umwandlung einfügen, damit pandoc die Wiki-Syntax nicht maskiert
    if "--mention-reporter" in flags and (r := reporter(key)):
        text = f"[~accountid:{r['accountId']}] " + text
    api("POST", f"/rest/api/2/issue/{key}/comment", {"body": text})


def attach(key, path):
    boundary = uuid.uuid4().hex
    with open(path, "rb") as fh:
        content = fh.read()
    ctype = mimetypes.guess_type(path)[0] or "text/plain"
    raw = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{os.path.basename(path)}\"\r\n"
           f"Content-Type: {ctype}\r\n\r\n").encode() + content + f"\r\n--{boundary}--\r\n".encode()
    api("POST", f"/rest/api/3/issue/{key}/attachments", raw=raw,
        headers={"X-Atlassian-Token": "no-check", "Content-Type": f"multipart/form-data; boundary={boundary}"})


def transition(key, target):
    transitions = api("GET", f"/rest/api/3/issue/{key}/transitions")["transitions"]
    match = next((t for t in transitions if t["to"]["name"].casefold() == target.casefold()), None)
    if not match:
        available = ", ".join(t["to"]["name"] for t in transitions)
        # Nicht fatal: ein fehlender Status im Board soll den Agent-Lauf nicht abbrechen
        print(f"::warning::Kein Übergang nach '{target}' für {key}. Möglich: {available}")
        return
    api("POST", f"/rest/api/3/issue/{key}/transitions", {"transition": {"id": match["id"]}})


def assign_reporter(key):
    f = api("GET", f"/rest/api/3/issue/{key}?fields=reporter,assignee")["fields"]
    r, a = f.get("reporter"), f.get("assignee")
    # Keine unnötige Zuweisung – sie würde in Jira erneut „Vorgang zugewiesen“ auslösen
    if r and (not a or a["accountId"] != r["accountId"]):
        api("PUT", f"/rest/api/3/issue/{key}/assignee", {"accountId": r["accountId"]})


def approval(key, status):
    """Gate 1 aus Jira ableiten – der Webhook-Payload wird bewusst nicht als Beweis genommen."""
    current = api("GET", f"/rest/api/3/issue/{key}?fields=status")["fields"]["status"]["name"]
    if current.casefold() != status.casefold():
        sys.exit(f"{key} steht auf '{current}', nicht auf '{status}' – keine Freigabe.")
    last, start = None, 0
    while True:
        page = api("GET", f"/rest/api/3/issue/{key}/changelog?startAt={start}&maxResults=100")
        for h in page["values"]:
            for item in h["items"]:
                if item["field"] == "status" and (item.get("toString") or "").casefold() == status.casefold():
                    last = h
        if page.get("isLast", True):
            break
        start += len(page["values"])
    if not last or "author" not in last:
        sys.exit(f"Kein Statuswechsel nach '{status}' im Verlauf von {key} gefunden.")
    author = last["author"]
    allowed = [a.strip() for a in os.environ.get("JIRA_APPROVERS", "").split(",") if a.strip()]
    if allowed and author["accountId"] not in allowed:
        sys.exit(f"{author['displayName']} ist nicht als Freigeber hinterlegt (JIRA_APPROVERS).")
    # Läuft die Pipeline mit dem Account eines Menschen, zählt dessen Freigabe nur, wenn er ausdrücklich
    # in JIRA_APPROVERS steht. Sicher, weil der Agent im CI keinen Jira-Zugriff hat und die Pipeline
    # selbst nie nach „Freigegeben“ verschiebt.
    if author["accountId"] == api("GET", "/rest/api/3/myself")["accountId"] and author["accountId"] not in allowed:
        sys.exit("Die Freigabe stammt vom Pipeline-User und dieser steht nicht in JIRA_APPROVERS – abgelehnt.")
    print(f"approver={author['displayName']}")
    print(f"approver_id={author['accountId']}")
    print(f"approved_at={last['created'][:10]}")


if __name__ == "__main__":
    cmds = {"fetch": fetch, "comment": comment, "attach": attach, "transition": transition,
            "assign-reporter": assign_reporter, "approval": approval}
    if len(sys.argv) < 3 or sys.argv[1] not in cmds:
        sys.exit(__doc__)
    cmds[sys.argv[1]](*sys.argv[2:])
