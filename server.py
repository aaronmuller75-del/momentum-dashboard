#!/usr/bin/env python3
"""
Aaron Müller – Realtor Dashboard Server
Serves the dashboard at http://localhost:5678
Run via LaunchAgent on login, or manually: python3 server.py
"""

import http.server
import os
import sys
import socket
import json
import glob
from urllib.parse import urlparse, parse_qs

PORT = 5678
DASHBOARD_DIR = os.path.expanduser("~/Desktop/Claude/Dashboard")
REPORTS_DIR   = os.path.expanduser("~/Desktop/Claude/Projects/Auto/Workspace")


def get_local_ip():
    """Return the Mac's LAN IP address (for iPad access)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("0.0.0.0", port)) == 0


ARCHIVE_DIR = os.path.expanduser("~/Desktop/Claude/Weekly Archives")


def save_weekly_archive(week_of, tasks):
    """Save a weekly task snapshot as a Markdown file."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    filepath = os.path.join(ARCHIVE_DIR, f"week-{week_of}.md")

    # Parse the date for a friendlier heading
    try:
        from datetime import datetime
        dt = datetime.strptime(week_of, "%Y-%m-%d")
        heading = dt.strftime("%-d %B %Y")          # e.g. 22 June 2026
    except Exception:
        heading = week_of

    completed  = [t for t in tasks if t.get("done")]
    incomplete = [t for t in tasks if not t.get("done")]

    lines = [
        f"# Week of {heading}\n",
        f"\n## ✅ Completed ({len(completed)})\n",
    ]
    for t in completed:
        lines.append(f"- [x] {t['text']}\n")
    lines.append(f"\n## ⬜ Not Completed ({len(incomplete)})\n")
    for t in incomplete:
        lines.append(f"- [ ] {t['text']}\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.writelines(lines)

    return filepath


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress request logs

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/update-prospect":
            length  = int(self.headers.get("Content-Length", 0))
            body    = json.loads(self.rfile.read(length))
            pid     = body.get("id")
            fields  = body.get("fields", {})
            listings_js = os.path.join(DASHBOARD_DIR, "data", "listings.js")
            try:
                with open(listings_js, "r", encoding="utf-8") as f:
                    raw = f.read()
                # Strip JS wrapper, parse JSON
                inner = raw.strip()
                inner = inner[inner.index("{"):]
                if inner.endswith(";"):
                    inner = inner[:-1]
                data = json.loads(inner)
                updated = False
                for p in data.get("prospects", []):
                    if p["id"] == pid:
                        p.update({k: v for k, v in fields.items() if v is not None})
                        updated = True
                        break
                if updated:
                    new_inner = json.dumps(data, indent=2, ensure_ascii=False)
                    with open(listings_js, "w", encoding="utf-8") as f:
                        f.write("window.DASH_LISTINGS = " + new_inner + ";\n")
                resp = json.dumps({"ok": updated}).encode()
            except Exception as e:
                resp = json.dumps({"ok": False, "error": str(e)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return

        if parsed.path == "/api/save-weekly-archive":
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))
            week_of = body.get("weekOf", "unknown")
            tasks   = body.get("tasks", [])
            try:
                filepath = save_weekly_archive(week_of, tasks)
                resp = json.dumps({"ok": True, "file": os.path.basename(filepath)}).encode()
            except Exception as e:
                resp = json.dumps({"ok": False, "error": str(e)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_error(404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path

        # ── /api/latest-report?prefix=PATTERN ──────────────────────────────
        # Returns {"url": "/reports/FILENAME"} for the newest matching file,
        # or {"error": "not found"} if none exist.
        if path == "/api/latest-report":
            qs     = parse_qs(parsed.query)
            prefix = qs.get("prefix", [""])[0]
            matches = sorted(
                glob.glob(os.path.join(REPORTS_DIR, prefix + "*.html")),
                reverse=True
            )
            if matches:
                filename = os.path.basename(matches[0])
                body = json.dumps({"url": f"/reports/{filename}"}).encode()
            else:
                body = json.dumps({"error": "not found"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # ── /reports/FILENAME ───────────────────────────────────────────────
        # Serves report HTML files from the Auto/Workspace directory.
        if path.startswith("/reports/"):
            filename = os.path.basename(path)          # strip any traversal
            filepath = os.path.join(REPORTS_DIR, filename)
            if os.path.isfile(filepath):
                with open(filepath, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404, f"Report not found: {filename}")
            return

        # ── everything else: serve from Dashboard directory ─────────────────
        super().do_GET()


if __name__ == "__main__":
    if is_port_in_use(PORT):
        ip = get_local_ip()
        print(f"Dashboard already running.")
        print(f"  Mac:  http://localhost:{PORT}/dashboard.html")
        print(f"  iPad: http://{ip}:{PORT}/dashboard.html")
        sys.exit(0)

    os.chdir(DASHBOARD_DIR)
    httpd = http.server.HTTPServer(("0.0.0.0", PORT), QuietHandler)
    ip = get_local_ip()
    print(f"✅ Realtor Dashboard running")
    print(f"   Mac:  http://localhost:{PORT}/dashboard.html")
    print(f"   iPad: http://{ip}:{PORT}/dashboard.html")
    print("   Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        httpd.server_close()
