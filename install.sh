#!/bin/bash
# ─────────────────────────────────────────────────────────────────
# Aaron Müller – Realtor Dashboard Installer
# Run once: bash ~/Desktop/Claude/Dashboard/install.sh
# ─────────────────────────────────────────────────────────────────
set -e

PLIST_SRC="$HOME/Desktop/Claude/Dashboard/com.aaronmuller.dashboard.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.aaronmuller.dashboard.plist"
DASHBOARD_URL="http://localhost:5678/dashboard.html"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Realtor Dashboard Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Copy LaunchAgent plist
echo "→ Installing LaunchAgent..."
cp "$PLIST_SRC" "$PLIST_DST"
chmod 644 "$PLIST_DST"

# 2. Unload if already loaded (ignore error if not)
launchctl unload "$PLIST_DST" 2>/dev/null || true

# 3. Load the LaunchAgent (starts server now + on every login)
launchctl load "$PLIST_DST"
echo "✅ LaunchAgent loaded — server will start on every login"

# 4. Wait a moment for the server to come up
sleep 2

# 5. Open the dashboard as a Chrome app window
echo "→ Opening dashboard..."
if [ -d "/Applications/Google Chrome.app" ]; then
  open -a "Google Chrome" --args \
    --app="$DASHBOARD_URL" \
    --window-size=1400,900 \
    --window-position=0,0
  echo "✅ Dashboard opened in Chrome app window"
elif [ -d "/Applications/Safari.app" ]; then
  open -a Safari "$DASHBOARD_URL"
  echo "✅ Dashboard opened in Safari (Chrome preferred for app-mode)"
else
  open "$DASHBOARD_URL"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Done! Dashboard is running at:"
echo "  $DASHBOARD_URL"
echo ""
echo "  To add to Dock:"
echo "  → Pin the Chrome window to your Dock"
echo "    (right-click the Chrome icon > Options > Keep in Dock)"
echo ""
echo "  To stop the server:"
echo "  launchctl unload ~/Library/LaunchAgents/com.aaronmuller.dashboard.plist"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
