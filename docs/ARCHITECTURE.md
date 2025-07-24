# Claude Buddy - Agent Hook System

## Overview

Claude Buddy provides a hook system for Claude Code that enables **Claude agents to activate hooks** which then **interface with MCP servers** to enhance functionality.

## Architecture Pattern

```
Claude Agents → Activate Hooks → Call MCP Servers → Enhanced Results
```

This pattern allows:
- **Multiple Claude agents** to trigger hooks concurrently
- **Hooks to leverage MCP servers** for external functionality  
- **Concurrency management** to handle resource limits
- **Clean separation** between hook logic and external tools

## Core Components

1. **Hook Protocol** (`src/hooks/base.py`)
   - Interface: `process_event(event_data) -> (should_continue, message)`
   - Supports concurrency management for multiple agents

2. **Hook Manager** (`src/hooks/manager.py`) 
   - Loads hooks from registry with concurrency manager
   - Routes events to appropriate hooks

3. **Concurrency Management** (`src/tools/concurrency/`)
   - Manages resource pools for concurrent agent operations
   - Prevents resource exhaustion when multiple agents run

4. **Registry** (`src/hooks/registry.json`)
   - Lists available hooks and their configurations

### Current Hooks

1. **post_tool_linter** - Fixes Python linting issues after file changes
2. **tdd_guard** - Validates TDD practices before code changes (PreToolUse)
3. **context7_docs** - Enhances context with current documentation via Context7 MCP (PreToolUse/PostToolUse)

## Directory Structure

```
claude_buddy/
├── src/
│   ├── hooks/
│   │   ├── base.py                 # Core hook interface with concurrency
│   │   ├── manager.py              # Hook loading with concurrency support
│   │   ├── registry.json           # Hook definitions
│   │   ├── post_tool_linter/       # Built-in linter hook  
│   │   ├── tdd_guard/              # TDD validation hook
│   │   └── context7_docs/          # Documentation enhancement hook
│   ├── tools/
│   │   └── concurrency/            # Resource pool management
│   └── tests/                      # Integration tests
└── CONTEXT7_MCP_SETUP.md          # MCP server configuration
```

## Hook Integration with MCP Servers

### Pattern: Hooks Call MCP Servers

```python
class Context7DocsHook(BaseHook):
    def process_event(self, event_data):
        # Hook detects when documentation needed
        libraries = self._detect_libraries(event_data)
        
        # Hook calls Context7 MCP server
        for library in libraries:
            docs = self._call_context7_mcp(library)
            context_enhancement += docs
            
        return True, context_enhancement
```

### MCP Server Setup

#### Context7 (Documentation Enhancement)
1. **Configure as MCP server** in Claude desktop config:
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["@upstash/context7-mcp"]
    }
  }
}
```

2. **Hook integration**: `context7_docs` hook automatically calls Context7 MCP when:
   - Before editing code with external libraries (PreToolUse)
   - After reading dependency files (PostToolUse)

#### TDD-Guard (Development Validation)  
1. **Install globally**: `npm install -g tdd-guard`
2. **Hook integration**: `tdd_guard` hook calls TDD-Guard CLI before code changes

## Creating a Hook

1. Create directory under `src/hooks/your_hook/`
2. Implement simple hook:

```python
from hooks.base import BaseHook

class YourHook(BaseHook):
    def process_event(self, event_data):
        # Keep it simple!
        return True, "Your message here"
    
    def get_config_schema(self):
        return {"type": "object", "properties": {"enabled": {"type": "boolean"}}}
```

3. Add to `registry.json`
4. Done!

## Testing

```bash
cd src
python3 tests/test_registry_integration.py
```

## Best Practices

1. **Keep hooks simple** - They should execute in milliseconds
2. **Don't manage external processes** - Use Claude Code's MCP instead  
3. **Fail gracefully** - Never crash Claude Code
4. **Be helpful** - Provide useful suggestions to users

This architecture is much simpler and aligns with Claude Code's design.