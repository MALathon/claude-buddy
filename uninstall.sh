#!/bin/bash
# Claude Buddy Uninstall Script

set -e

echo "🧹 Uninstalling Claude Buddy..."

# Remove src virtual environment
if [ -d "src/.venv" ]; then
    echo "🗑️  Removing Python virtual environment (src/.venv)..."
    rm -rf src/.venv
fi

# Remove root virtual environment (if exists from old install)
if [ -d ".venv" ]; then
    echo "🗑️  Removing old root virtual environment..."
    rm -rf .venv
fi

# Remove src node_modules
if [ -d "src/node_modules" ]; then
    echo "🗑️  Removing Node.js dependencies (src/node_modules)..."
    rm -rf src/node_modules
fi

# Remove root node_modules (if exists from old install)
if [ -d "node_modules" ]; then
    echo "🗑️  Removing old root node_modules..."
    rm -rf node_modules
fi

# Remove package-lock.json files
if [ -f "src/package-lock.json" ]; then
    echo "🗑️  Removing src/package-lock.json..."
    rm -f src/package-lock.json
fi
if [ -f "package-lock.json" ]; then
    echo "🗑️  Removing package-lock.json..."
    rm -f package-lock.json
fi

# Remove test artifacts
echo "🗑️  Cleaning up test artifacts..."
rm -f test_*.json test_*.txt debug.log

# Remove .claude directory
if [ -d ".claude" ]; then
    echo "🗑️  Removing .claude directory..."
    rm -rf .claude
fi

# Remove Python cache
echo "🗑️  Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

echo ""
echo "✅ Claude Buddy uninstalled!"
echo ""
echo "📚 To reinstall, run: ./install.sh"