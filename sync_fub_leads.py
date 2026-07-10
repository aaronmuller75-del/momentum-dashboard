#!/usr/bin/env python3
"""
Follow Up Boss → Dashboard Lead Sync
Fetches recent leads directly from the FUB API and writes data/fub_leads.js
Run this manually or schedule it (e.g. every 15 minutes via launchd/cron).
"""

import json, os, sys, urllib.request, urllib.error, base64
from datetime import datetime, timezone, timedelta

# ── CONFIG ──
API_KEY   = "fka_1eWpEhC06EHGY5zBtE6yE43piglwGt467I"   # Replace after regenerating
BASE_URL  = "https://api.followupboss.com/v1"
OUT_DIR   = os.path.join(os.path.dirname(__file__), "data")
OUT_FILE  = os.path.join(OUT_DIR, "fub_leads.js")
# Pull leads created in the last N days for the response timer + aging queue
DAYS_BACK = 30

def fub_get(path, params=None):
    url = BASE_URL + path
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    token = base64.b64encode(f"{API_KEY}:".encode()).decode()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
        "X-System": "Aaron-Dashboard",
        "X-System-Key": API_KEY,
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def main():
    print("Fetching leads from Follow Up Boss...")
    since = (datetime.now(timezone.utc) - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%dT%H:%M:%SZ")

    try:
        data = fub_get("/people", {
            "sort": "created",
            "sortDirection": "desc",
            "limit": 100,
            "createdAfter": since,
        })
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        error_msg = f"FUB API error {e.code}: {body}"
        print(f"ERROR: {error_msg}", file=sys.stderr)
        write_js([], error_msg)
        sys.exit(1)
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}", file=sys.stderr)
        write_js([], error_msg)
        sys.exit(1)

    people = data.get("people", [])
    print(f"  Got {len(people)} people from FUB")

    leads = []
    for p in people:
        # Pick the best phone + email
        phones = p.get("phones", []) or []
        emails = p.get("emails", []) or []
        phone  = phones[0].get("value","") if phones else ""
        email  = emails[0].get("value","") if emails else ""

        # Source / stage
        source = ""
        tags   = p.get("tags", []) or []
        if isinstance(tags, list) and tags:
            source = tags[0] if isinstance(tags[0], str) else ""
        if not source:
            source = (p.get("source") or {}).get("name","CINC") if isinstance(p.get("source"),dict) else p.get("source","CINC")

        stage    = p.get("stage","New") or "New"
        assigned = ""
        assignee = p.get("assignedTo") or {}
        if isinstance(assignee, dict):
            assigned = assignee.get("name","")

        leads.append({
            "id":         str(p.get("id","")),
            "name":       p.get("name","Unknown"),
            "phone":      phone,
            "email":      email,
            "source":     source,
            "stage":      stage,
            "assignedTo": assigned,
            "receivedAt": p.get("created",""),
            "notes":      p.get("lastNote","") or "",
            "budget":     "",
        })

    write_js(leads, None)
    print(f"  Written {len(leads)} leads to {OUT_FILE}")

def write_js(leads, error):
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    payload = {
        "_comment":   "Auto-populated by sync_fub_leads.py from Follow Up Boss API directly.",
        "leads":      leads,
        "lastUpdated": now,
        "source":     "Follow Up Boss API (direct)",
    }
    if error:
        payload["_error"] = error

    os.makedirs(OUT_DIR, exist_ok=True)
    js = "window.DASH_LEADS = " + json.dumps(payload, indent=2) + ";"
    with open(OUT_FILE, "w") as f:
        f.write(js)

if __name__ == "__main__":
    main()
