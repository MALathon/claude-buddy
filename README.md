# Claude Buddy

Hook system for Claude Code that enables **Claude agents to activate hooks** which then **interface with MCP servers** and external tools to enhance functionality.

## Quick Start

### 1. Set up Context7 MCP Server
```bash
# Add Context7 MCP server for up-to-date documentation
claude mcp add --transport http context7 https://mcp.context7.com/mcp

# Verify it's connected
claude mcp list
```

### 2. Install Claude Buddy

**Quick Install (Recommended):**
```bash
# Download and run the installer directly (bypasses cache)
curl -sSL "https://raw.githubusercontent.com/MALathon/claude-buddy/main/install.sh?$(date +%s)" | bash
```

**Manual Install:**
```bash
# Clone the repository
git clone https://github.com/MALathon/claude-buddy.git
cd claude-buddy

# Run the installation script
./install.sh

# Or install manually:
pip install -r requirements.txt
npm install  # Installs TDD-Guard locally
```

## 📁 Repository Structure

```
claude-buddy/
├── src/                    # Core source code
│   ├── hooks/             # Hook implementations
│   │   ├── post_tool_linter/  # Auto-fix Python linting
│   │   ├── context7_docs/     # Documentation enhancement  
│   │   ├── tdd_guard/         # Test-driven development
│   │   └── unified_logger.py  # Logging system
│   ├── tools/             # Shared utilities
│   │   └── concurrency/   # Resource management
│   └── tests/             # Organized test suite
│       ├── demos/         # Interactive demonstrations
│       ├── integration/   # End-to-end tests
│       ├── components/    # Unit tests
│       ├── concurrency/   # Performance tests
│       └── scenarios/     # Real-world usage tests
├── config/                # Configuration files
│   ├── claude_code_settings.json
│   ├── pyrightconfig.json
│   ├── mypy.ini
│   └── pytest.ini
├── scripts/               # Utility scripts
│   ├── debug_*.py        # Debugging tools
│   └── check_*.py        # Validation scripts
├── docs/                  # Documentation
│   ├── ARCHITECTURE.md   # System design
│   └── roadmap.md        # Development roadmap
└── logs/                  # Runtime logs (auto-created)
    ├── claude_buddy_*.log     # Unified logs
    ├── post_tool_linter/      # Component-specific
    ├── context7/              # Component-specific
    └── tdd_guard/             # Component-specific
```

## Architecture

```
Claude Agents → Activate Hooks → Call MCP Servers/External Tools → Enhanced Results
```

## Available Hooks

### Core Hooks
- **`post_tool_linter`** - Auto-fixes Python linting issues after file modifications (PostToolUse)
- **`context7_docs`** - Enhances Claude's context with current library documentation via Context7 MCP (PreToolUse) 
- **`tdd_guard`** - Enforces Test-Driven Development practices before code changes (PreToolUse)

### MCP Integration
- **Context7**: Provides up-to-date documentation for libraries to prevent hallucinated APIs
- **HTTP Transport**: `https://mcp.context7.com/mcp` 
- **PreToolUse Pattern**: Injects current docs BEFORE Claude writes code

### External Tools
- **TDD-Guard**: Available globally via `npm install -g tdd-guard`
- **Fallback Chain**: Submodule → Global → Graceful degradation

## Usage Commands
- `/buddy list` - List available hooks
- `/buddy enable <hook>` - Enable specific hook
- `/buddy disable <hook>` - Disable specific hook  
- `/buddy-test` - Run comprehensive integration tests

## Testing
```bash
# Run end-to-end integration tests
python3 tests/test_end_to_end.py

# Run all tests
python3 -m pytest tests/ -v
```

## 🚀 Quick Reference

### Run Interactive Demos
```bash
# Post-Tool Linter concurrency demo
python src/tests/demos/test_post_linter_demo.py

# Context7 documentation enhancement
python src/tests/demos/test_context7_demo.py

# TDD-Guard test enforcement
python src/tests/demos/test_tdd_guard_demo.py

# Unified logging system
python src/tests/demos/test_unified_logging_demo.py
```

### Run Test Suite
```bash
# All tests
python -m pytest src/tests/ -v

# Specific category
python -m pytest src/tests/integration/ -v
python -m pytest src/tests/concurrency/ -v
```

### View Logs
```bash
# Real-time unified logs
tail -f logs/claude_buddy_$(date +%Y-%m-%d).log

# Component-specific logs
tail -f logs/post_tool_linter/$(date +%Y-%m-%d).log
```

### Debug Tools
```bash
# Check Context7 MCP server
python scripts/debug_context7_detection.py

# Test MCP communication
python scripts/debug_mcp_call.py

# Validate code fixes
python scripts/check_actual_fixes.py
```

## Configuration

### Timeout Settings
Claude Buddy uses proper timeout values to prevent premature termination:
- **Bash commands**: 30 minutes (set via `.env`)
- **TDD-Guard validation**: 5 minutes 
- **External tool checks**: 30 seconds
- **MCP operations**: 30 minutes

### Hook Configuration
Hooks are configured via `hooks/registry.json` and individual config files:
- `hooks/context7_docs/config.json` - Context7 documentation settings
- `hooks/tdd_guard/config.json` - TDD validation settings (timeout: 300s)
- `hooks/post_tool_linter/config.json` - Linting behavior settings

## Concurrency Management

Built-in resource management for multiple Claude agents:
- Resource pools prevent conflicts
- Configurable timeouts and limits
- Clean cleanup procedures