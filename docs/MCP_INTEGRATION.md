# MCP Integration in Claude Buddy

## Overview

Claude Buddy integrates with MCP (Model Context Protocol) servers to enhance Claude's capabilities. The primary MCP integration is with Context7 for library documentation.

## How MCP Works in Claude Code

MCP servers are external processes that Claude Code can communicate with to:
- Fetch documentation (Context7)
- Access databases
- Interact with external APIs
- Provide specialized tools

## Context7 MCP Setup

### Automatic Setup (via install.sh)

The installation script automatically configures Context7:

```bash
# During installation
./install.sh

# This runs:
claude mcp add --transport http context7 https://mcp.context7.com/mcp
```

### Manual Setup

If you need to set up Context7 manually:

```bash
# Add Context7 MCP server
claude mcp add --transport http context7 https://mcp.context7.com/mcp

# Verify it's configured
claude mcp list

# Check Context7 details
claude mcp get context7
```

## How Context7 Hook Uses MCP

### 1. Library Detection
When Claude is about to write code, the Context7 hook:
- Analyzes the code for library imports
- Detects framework patterns
- Identifies relevant documentation needs

### 2. MCP Communication Flow

```
User: "Create a FastAPI endpoint"
         ↓
Claude prepares code with imports
         ↓
Context7 Hook detects "fastapi"
         ↓
Hook prepares MCP request
         ↓
Claude Code MCP system calls Context7
         ↓
Context7 returns documentation
         ↓
Claude generates better code
```

### 3. The Natural Language Challenge

Current limitation: Context7 only sees the code Claude is about to write, not the user's original intent.

**Example Problem:**
- User says: "Build an API with authentication"
- Claude starts writing: `from fastapi import FastAPI`
- Context7 sees: Only "fastapi", not "authentication" context

**Solution Approaches:**

1. **Enhanced Detection**: Look for auth-related imports
2. **File Context**: Use filename (auth.py → authentication topic)
3. **Comment Analysis**: Parse docstrings for intent
4. **Historical Context**: Track previous requests in session

## MCP Server Types

### HTTP Transport (Context7)
```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp
```
- Best for: Remote services
- Authentication: Built-in
- Performance: Network dependent

### Stdio Transport
```bash
claude mcp add my-server --transport stdio -- /path/to/server
```
- Best for: Local tools
- Authentication: Not needed
- Performance: Fast

### SSE Transport
```bash
claude mcp add --transport sse server https://example.com/sse
```
- Best for: Real-time updates
- Authentication: Token-based
- Performance: Low latency

## Testing MCP Integration

### 1. Verify Context7 is Available

```python
# In your project
from claude_buddy.hooks.external_loader import get_external_loader
loader = get_external_loader()
print(loader.is_tool_available('context7'))
```

### 2. Test Documentation Fetch

Create a test file:
```python
# test_api.py
from fastapi import FastAPI
app = FastAPI()
```

Watch Claude Code logs to see MCP communication.

### 3. Check Hook Integration

```python
# Enable verbose logging
export CLAUDE_BUDDY_DEBUG=true
# Run Claude Code and create FastAPI code
```

## Troubleshooting

### "MCP server not available"
1. Check `claude mcp list`
2. Restart Claude Code
3. Check network connectivity

### "No documentation returned"
1. Library might not be in Context7
2. Check MCP server logs
3. Try different library names

### Performance Issues
1. MCP calls add latency
2. Cache documentation locally
3. Limit concurrent MCP calls

## Advanced: Custom MCP Servers

You can create custom MCP servers for your organization:

```javascript
// my-mcp-server.js
import { Server } from '@modelcontextprotocol/sdk';

const server = new Server({
  name: 'my-docs',
  version: '1.0.0',
});

server.setRequestHandler('get-docs', async (params) => {
  // Return your custom documentation
  return {
    content: "Your documentation here"
  };
});

server.start();
```

Then add it:
```bash
claude mcp add my-docs --transport stdio -- node my-mcp-server.js
```

## Security Considerations

1. **Trust**: Only add MCP servers you trust
2. **Scope**: Use local scope for project-specific servers
3. **Credentials**: Use environment variables for secrets
4. **Network**: HTTP transport exposes data over network

## Future Enhancements

### Natural Language Intent Capture
```python
# Proposed enhancement
class EnhancedContext7Hook:
    def capture_user_intent(self, message):
        # Extract topics from natural language
        topics = self.nlp_extract_topics(message)
        self.session_context['topics'] = topics
        
    def get_documentation(self, library):
        # Use captured intent
        topic = self.session_context.get('topics', {}).get(library)
        return self.mcp_fetch(library, topic)
```

### Predictive Documentation
```python
# Based on file patterns
if 'auth' in filename:
    preload_docs(['jwt', 'oauth2', 'bcrypt'])
elif 'test_' in filename:
    preload_docs(['pytest', 'unittest'])
```

This would make Context7 more proactive in providing relevant documentation.