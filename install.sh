#!/bin/bash
# Claude Buddy Installation Script
# Installs Claude Buddy hooks into user's project .claude directory

set -e

echo "🚀 Installing Claude Buddy into your project..."

# Determine if this is development install (in claude-buddy repo) or user install
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if we're in a Claude Buddy repository
if [[ -f "$SCRIPT_DIR/src/hooks/registry.json" ]]; then
    echo "🔧 Development installation detected (script directory)"
    INSTALL_MODE="dev"
    REPO_ROOT="$SCRIPT_DIR"
elif [[ "$(basename "$(pwd)")" == "claude_buddy" ]] || [[ -f "src/hooks/registry.json" ]]; then
    echo "🔧 Development installation detected (current directory)"
    INSTALL_MODE="dev"
    REPO_ROOT=$(pwd)
elif [[ -f "$SCRIPT_DIR/../src/hooks/registry.json" ]]; then
    echo "🔧 Development installation detected (parent directory)"
    INSTALL_MODE="dev"  
    REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    echo "👤 User installation detected"
    INSTALL_MODE="user"
    # For user installs, we need to download source from GitHub
    TEMP_DIR=$(mktemp -d)
    echo "📥 Downloading Claude Buddy source..."
    
    # Download the latest release from GitHub
    if ! curl -L -o "$TEMP_DIR/claude-buddy.tar.gz" "https://github.com/MALathon/claude-buddy/archive/refs/heads/main.tar.gz"; then
        echo "❌ Error: Failed to download Claude Buddy from GitHub"
        echo "   Please check your internet connection or clone the repository manually:"
        echo "   git clone https://github.com/MALathon/claude-buddy.git"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    # Extract the archive
    echo "📦 Extracting Claude Buddy..."
    if ! tar -xzf "$TEMP_DIR/claude-buddy.tar.gz" -C "$TEMP_DIR"; then
        echo "❌ Error: Failed to extract Claude Buddy archive"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
    
    REPO_ROOT="$TEMP_DIR/claude-buddy-main"
    
    # Verify the extraction
    if [[ ! -f "$REPO_ROOT/src/hooks/registry.json" ]]; then
        echo "❌ Error: Invalid Claude Buddy archive structure"
        echo "   Expected to find src/hooks/registry.json"
        rm -rf "$TEMP_DIR"
        exit 1
    fi
fi

USER_PROJECT_DIR=$(pwd)

# Check Python version
echo "📦 Checking Python version..."
python3 --version

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed. Please install Node.js (>=14.0.0) first."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "📦 Node.js version: $(node --version)"

# Install Context7 MCP server globally
echo "📦 Installing Context7 MCP server..."
if npm list -g @upstash/context7-mcp &> /dev/null; then
    echo "✅ Context7 MCP server already installed globally"
else
    npm install -g @upstash/context7-mcp@latest
    echo "✅ Context7 MCP server installed globally"
fi

# Install TDD-Guard globally
echo "📦 Installing TDD-Guard..."
if npm list -g tdd-guard &> /dev/null; then
    echo "✅ TDD-Guard already installed globally"
else
    npm install -g tdd-guard@latest
    echo "✅ TDD-Guard installed globally"
fi

# Configure Context7 with Claude CLI's MCP system
echo "🔧 Configuring Context7 MCP server with Claude CLI..."
if command -v claude &> /dev/null; then
    # Check if Context7 is already configured
    if claude mcp list 2>/dev/null | grep -q "context7"; then
        echo "✅ Context7 MCP server already configured in Claude CLI"
    else
        echo "📝 Adding Context7 to Claude MCP servers..."
        # Try to add Context7 automatically
        # Use HTTP transport for better reliability
        if claude mcp add -t http context7 'https://mcp.context7.com/mcp' 2>/dev/null; then
            echo "✅ Context7 MCP server successfully configured in Claude CLI (HTTP mode)"
        else
            # Fallback to stdio mode
            if claude mcp add context7 'npx @upstash/context7-mcp' 2>/dev/null; then
                echo "✅ Context7 MCP server successfully configured in Claude CLI (stdio mode)"
            else
                echo "⚠️  Could not automatically configure Context7 MCP server"
                echo "   Please run manually: claude mcp add context7 'npx @upstash/context7-mcp'"
            fi
        fi
    fi
else
    echo "⚠️  Claude CLI not found. Context7 MCP configuration skipped."
    echo "   Install Claude CLI to enable MCP features."
fi

# Create .claude directory structure in user's project
echo "📁 Setting up .claude directory structure..."
mkdir -p "$USER_PROJECT_DIR/.claude/claude_buddy"
mkdir -p "$USER_PROJECT_DIR/.claude/claude_buddy/logs"
mkdir -p "$USER_PROJECT_DIR/.claude/commands"

# Copy Claude Buddy source code to .claude/claude_buddy
echo "📦 Installing Claude Buddy system..."
# Use rsync to exclude .claude directories and other unwanted files
rsync -av --exclude=".claude" --exclude="__pycache__" --exclude="*.pyc" "$REPO_ROOT/src/" "$USER_PROJECT_DIR/.claude/claude_buddy/"

# Create Python virtual environment in .claude/claude_buddy
echo "🔧 Creating virtual environment for Claude Buddy..."
cd "$USER_PROJECT_DIR/.claude/claude_buddy"
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
echo "📦 Installing Claude Buddy Python dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install -r "$REPO_ROOT/requirements.txt"
fi

# Install Node.js dependencies locally
echo "📦 Installing Node.js dependencies..."
if [ -f "package.json" ]; then
    npm install
fi

# Create hook manager script
echo "🔧 Creating hook manager..."
cat > "$USER_PROJECT_DIR/.claude/claude_buddy/hook_manager.py" << 'EOF'
#!/usr/bin/env python3
"""Claude Buddy Hook Manager - Entry point for Claude Code hooks."""

import json
import sys
import os
from pathlib import Path

# Activate virtual environment by modifying sys.path
venv_site_packages = Path(__file__).parent / ".venv" / "lib" / "python3.12" / "site-packages"
if not venv_site_packages.exists():
    # Try different Python versions
    for py_ver in ["python3.11", "python3.10", "python3.9", "python3.8"]:
        venv_site_packages = Path(__file__).parent / ".venv" / "lib" / py_ver / "site-packages"
        if venv_site_packages.exists():
            break

if venv_site_packages.exists():
    sys.path.insert(0, str(venv_site_packages))

# Add claude_buddy to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    # Debug path information
    import os
    debug_info = f"Python path: {sys.path}\\nCWD: {os.getcwd()}\\nScript path: {Path(__file__).parent}"
    
    from hooks.unified_logger import init_unified_logging, ComponentType, LogLevel
    from tools.concurrency.concurrency import GlobalConcurrencyManager
    
    # Initialize logger globally so all hooks use the same instance
    log_dir = Path(__file__).parent / "logs"
    global_logger = init_unified_logging(base_dir=log_dir, enable_streaming=False)
    global_logger.log(ComponentType.SYSTEM, LogLevel.INFO, f"📁 Logs directory: {log_dir}")
    
    def load_registry():
        """Load the hook registry."""
        registry_path = Path(__file__).parent / "hooks" / "registry.json"
        if not registry_path.exists():
            return {"hooks": {}}
        
        with open(registry_path) as f:
            return json.load(f)

    def get_enabled_hooks(event_type):
        """Get hooks that should run for the given event type."""
        registry = load_registry()
        enabled_hooks = []
        
        for hook_name, hook_config in registry.get("hooks", {}).items():
            if event_type in hook_config.get("events", []):
                config_file = Path(__file__).parent / "hooks" / hook_config.get("config_file", "")
                if config_file.exists():
                    try:
                        with open(config_file) as f:
                            config = json.load(f)
                        if config.get("enabled", hook_config.get("enabled_by_default", False)):
                            enabled_hooks.append({
                                "name": hook_name,
                                "config": hook_config,
                                "settings": config
                            })
                    except Exception as e:
                        print(f"Warning: Could not load config for {hook_name}: {e}", file=sys.stderr)
        
        return enabled_hooks

    def run_hook(hook_info, event_data):
        """Run a single hook."""
        hook_name = hook_info["name"]
        hook_config = hook_info["config"]
        
        try:
            entry_point = hook_config.get("entry_point", "")
            if not entry_point:
                return True
            
            # Import the hook module
            module_path = entry_point.replace("/", ".").replace(".py", "")
            module = __import__(module_path, fromlist=["create_hook"])
            
            # Create hook instance
            concurrency_manager = GlobalConcurrencyManager()
            hook_instance = module.create_hook(hook_info["settings"], concurrency_manager)
            
            # Process the event
            should_continue, message = hook_instance.process_event(event_data)
            
            if message:
                print(message, file=sys.stderr)
            
            return should_continue
            
        except Exception as e:
            print(f"Error running hook {hook_name}: {e}", file=sys.stderr)
            return True  # Don't block on hook errors

    def main():
        """Main entry point."""
        if len(sys.argv) < 2:
            print("Usage: python hook_manager.py <event_type>", file=sys.stderr)
            sys.exit(1)
        
        event_type = sys.argv[1]
        
        # Use the global logger instance
        logger = global_logger
        logger.log(ComponentType.SYSTEM, LogLevel.INFO, f"🎣 Claude Buddy hook: {event_type}")
        
        try:
            # Read event data from stdin
            event_data_raw = sys.stdin.read()
            if event_data_raw.strip():
                event_data = json.loads(event_data_raw)
            else:
                event_data = {"event_type": event_type}
            
            event_data["event_type"] = event_type
            
            # Log ALL Claude events (not just Claude Buddy events)
            tool_name = event_data.get("tool_name", "unknown")
            tool_input = event_data.get("tool_input", {})
            
            # Log the raw event for complete visibility
            logger.log(
                ComponentType.SYSTEM, 
                LogLevel.INFO, 
                f"Claude Event: {event_type} - Tool: {tool_name}",
                metadata={
                    "event_type": event_type,
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "full_event": event_data
                }
            )
            
            # Get and run enabled hooks
            enabled_hooks = get_enabled_hooks(event_type)
            
            if not enabled_hooks:
                logger.log(ComponentType.SYSTEM, LogLevel.DEBUG, f"No hooks enabled for {event_type}")
                sys.exit(0)
            
            logger.log(ComponentType.SYSTEM, LogLevel.INFO, f"Running {len(enabled_hooks)} hooks for {event_type}")
            
            all_success = True
            for hook_info in enabled_hooks:
                hook_name = hook_info["name"]
                logger.log(ComponentType.SYSTEM, LogLevel.INFO, f"Executing hook: {hook_name}")
                
                success = run_hook(hook_info, event_data)
                
                if not success:
                    logger.log(ComponentType.SYSTEM, LogLevel.ERROR, f"Hook failed: {hook_name}")
                    all_success = False
                else:
                    logger.log(ComponentType.SYSTEM, LogLevel.SUCCESS, f"Hook completed: {hook_name}")
            
            logger.log(ComponentType.SYSTEM, LogLevel.INFO, f"All hooks completed for {event_type}")
            sys.exit(0 if all_success else 1)
            
        except Exception as e:
            logger.log(ComponentType.SYSTEM, LogLevel.ERROR, f"Hook manager error: {e}", metadata={"error": str(e)})
            print(f"Hook manager error: {e}", file=sys.stderr)
            sys.exit(1)

    if __name__ == "__main__":
        main()

except ImportError as e:
    # Create debug log for troubleshooting
    debug_file = Path(__file__).parent / "debug_import.log"
    with open(debug_file, "w") as f:
        f.write(f"Import error: {e}\\n")
        f.write(f"Python version: {sys.version}\\n")
        f.write(f"Python path: {sys.path}\\n")
        f.write(f"Working directory: {os.getcwd()}\\n")
        f.write(f"Script directory: {Path(__file__).parent}\\n")
        f.write(f"Files in script directory: {list(Path(__file__).parent.iterdir())}\\n")
    
    print(f"Claude Buddy import error: {e}", file=sys.stderr)
    print(f"Debug info written to: {debug_file}", file=sys.stderr)
    sys.exit(0)  # Don't block if our system isn't working
EOF

# Make hook manager executable
chmod +x "$USER_PROJECT_DIR/.claude/claude_buddy/hook_manager.py"

# Create MCP diagnostic script
cat > "$USER_PROJECT_DIR/.claude/claude_buddy/diagnose_mcp.py" << 'EOF'
#!/usr/bin/env python3
"""MCP Server Diagnostic Tool."""

import subprocess
import json
from pathlib import Path

def check_mcp_server():
    """Check if Context7 MCP server is accessible."""
    print("🔍 Checking MCP Server Status...")
    
    try:
        # Check if claude CLI is available
        result = subprocess.run(['claude', '--version'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ Claude CLI not found or not working")
            return False
        print(f"✅ Claude CLI version: {result.stdout.strip()}")
        
        # Check MCP servers
        result = subprocess.run(['claude', 'mcp', 'list'], capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"❌ MCP list failed: {result.stderr}")
            return False
            
        print("📋 MCP Servers:")
        print(result.stdout)
        
        if 'context7' in result.stdout.lower():
            print("✅ Context7 MCP server found")
            return True
        else:
            print("⚠️  Context7 MCP server not found in list")
            return False
            
    except Exception as e:
        print(f"❌ MCP check failed: {e}")
        return False

if __name__ == "__main__":
    check_mcp_server()
EOF

chmod +x "$USER_PROJECT_DIR/.claude/claude_buddy/diagnose_mcp.py"

# Merge with existing .claude/settings.json or create new one
echo "🔧 Configuring Claude Code hooks..."
SETTINGS_FILE="$USER_PROJECT_DIR/.claude/settings.json"

if [ -f "$SETTINGS_FILE" ]; then
    echo "📝 Merging with existing .claude/settings.json..."
    # Backup existing settings
    cp "$SETTINGS_FILE" "$SETTINGS_FILE.backup"
    
    # Use Python to merge JSON (safer than manual editing)
    python3 << EOF
import json
from pathlib import Path

settings_file = Path("$SETTINGS_FILE")
if settings_file.exists():
    with open(settings_file) as f:
        settings = json.load(f)
else:
    settings = {}

# Ensure hooks section exists
if "hooks" not in settings:
    settings["hooks"] = {}

# Add Claude Buddy hooks - no matcher field means it applies to all tools
# Use absolute path to avoid path duplication issues
hook_manager_path = str(Path("$USER_PROJECT_DIR").absolute() / ".claude" / "claude_buddy" / "hook_manager.py")

claude_buddy_hooks = {
    "PreToolUse": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": f"python3 {hook_manager_path} PreToolUse",
                    "description": "Claude Buddy - TDD-Guard and Context7 validation"
                }
            ]
        }
    ],
    "PostToolUse": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": f"python3 {hook_manager_path} PostToolUse",
                    "description": "Claude Buddy - Post-Tool Linter and Context7 enhancement"
                }
            ]
        }
    ]
}

for event_type, hook_configs in claude_buddy_hooks.items():
    if event_type not in settings["hooks"]:
        settings["hooks"][event_type] = []
    
    # Remove any existing Claude Buddy hooks (with old or new format)
    settings["hooks"][event_type] = [
        matcher_config for matcher_config in settings["hooks"][event_type]
        if not any("claude_buddy" in str(hook.get("command", ""))
                   for hook in matcher_config.get("hooks", []))
    ]
    
    # Add the new format hooks
    settings["hooks"][event_type].extend(hook_configs)

with open(settings_file, "w") as f:
    json.dump(settings, f, indent=2)
EOF
else
    echo "📝 Creating new .claude/settings.json..."
    # Use absolute path for hooks
    HOOK_MANAGER_PATH="$USER_PROJECT_DIR/.claude/claude_buddy/hook_manager.py"
    cat > "$SETTINGS_FILE" << EOF
{
  "hooks": {
    "PreToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOOK_MANAGER_PATH PreToolUse",
            "description": "Claude Buddy - TDD-Guard and Context7 validation"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 $HOOK_MANAGER_PATH PostToolUse",
            "description": "Claude Buddy - Post-Tool Linter and Context7 enhancement"
          }
        ]
      }
    ]
  }
}
EOF
fi

# Copy slash commands
echo "📝 Installing Claude Buddy slash commands..."
if [ -d "$REPO_ROOT/src/.claude/commands" ]; then
    cp -r "$REPO_ROOT/src/.claude/commands/"* "$USER_PROJECT_DIR/.claude/commands/" 2>/dev/null || true
elif [ -d "$USER_PROJECT_DIR/.claude/claude_buddy/.claude/commands" ]; then
    # Commands were already copied with the src directory
    cp -r "$USER_PROJECT_DIR/.claude/claude_buddy/.claude/commands/"* "$USER_PROJECT_DIR/.claude/commands/" 2>/dev/null || true
fi

# Copy .env.example if it doesn't exist in user project
echo "📝 Installing environment configuration template..."
if [ -f "$REPO_ROOT/.env.example" ] && [ ! -f "$USER_PROJECT_DIR/.env.example" ]; then
    cp "$REPO_ROOT/.env.example" "$USER_PROJECT_DIR/.env.example"
    echo "   📄 Copied .env.example - customize timeout settings as needed"
fi

# Clean up temporary directory for user installs
if [[ "$INSTALL_MODE" == "user" ]]; then
    rm -rf "$TEMP_DIR"
fi

# Return to original directory
cd "$USER_PROJECT_DIR"

echo ""
echo "✅ Claude Buddy installation complete!"
echo ""
echo "📚 Installation summary:"
echo "   - Claude Buddy system: .claude/claude_buddy/"
echo "   - Python virtual environment: .claude/claude_buddy/.venv"
echo "   - Hook integration: .claude/settings.json"
echo "   - Slash commands: .claude/commands/"
echo "   - Environment template: .env.example"
echo ""
echo "🎯 Claude Buddy is now active in your project!"
echo "   - TDD-Guard will enforce test-first development on PreToolUse"
echo "   - Post-Tool Linter will auto-fix Python code issues on PostToolUse"
echo "   - Context7 will provide real-time library documentation"
echo "   - Use /buddy-hooks, /test, /debug slash commands for management"
echo ""
echo "⚡ External Tools Status:"
if command -v tdd-guard &> /dev/null; then
    echo "   ✅ TDD-Guard: Installed"
else
    echo "   ❌ TDD-Guard: Not found"
fi
if command -v claude &> /dev/null && claude mcp list 2>/dev/null | grep -q "context7"; then
    echo "   ✅ Context7 MCP: Configured"
else
    echo "   ⚠️  Context7 MCP: Requires manual configuration"
fi
echo ""
echo "🔧 Configuration:"
echo "   - Hook settings: .claude/claude_buddy/hooks/*/config.json"
echo "   - Timeout settings: Copy .env.example to .env and customize"
echo "   - Enable/disable hooks by editing config files"
echo "   - View logs: tail -f .claude/claude_buddy/logs/claude_buddy_*.log"
echo ""
echo "🔍 Troubleshooting:"
echo "   - Test hook manager: python .claude/claude_buddy/hook_manager.py PostToolUse"
echo "   - Check MCP server: python .claude/claude_buddy/diagnose_mcp.py"
echo "   - View import debug: cat .claude/claude_buddy/debug_import.log"
echo ""
echo "⚠️  Note: Restart Claude Code to activate the new hooks"