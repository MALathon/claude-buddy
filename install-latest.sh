#!/bin/bash
# Claude Buddy Latest Installer - Always gets the freshest version

echo "🚀 Installing latest Claude Buddy (cache-busted)..."

# Use timestamp to ensure we bypass any CDN caching
TIMESTAMP=$(date +%s)
INSTALL_URL="https://raw.githubusercontent.com/MALathon/claude-buddy/main/install.sh?t=${TIMESTAMP}"

echo "📥 Downloading from: $INSTALL_URL"

# Download with no-cache headers and timestamp
curl -H 'Cache-Control: no-cache' \
     -H 'Pragma: no-cache' \
     -sSL \
     "$INSTALL_URL" | bash

echo "✅ Installation complete!"