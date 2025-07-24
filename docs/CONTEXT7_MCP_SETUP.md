# Context7 MCP Server Setup

## Overview

Context7 provides library documentation through an MCP (Model Context Protocol) server. When properly configured, it enhances Claude's code generation with current, version-specific documentation.

## How Context7 Works

1. **Library Detection**: Context7 analyzes code Claude is about to write
2. **MCP Tools**: Uses two MCP tools to fetch documentation:
   - `resolve-library-id`: Converts library names to Context7 IDs
   - `get-library-docs`: Fetches actual documentation

3. **Natural Language Gap**: Context7 can also capture intent from user messages

## Installation & Setup

### 1. Install Context7 MCP Server

The Context7 MCP server is automatically configured when you install Claude Buddy:

```bash
# During Claude Buddy installation
./install.sh
```

This adds to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"],
      "env": {}
    }
  }
}
```

### 2. Verify MCP Server

Check if Context7 is available:

```bash
# In your project
python -c "from claude_buddy.hooks.external_loader import get_external_loader; print(get_external_loader().is_tool_available('context7'))"
```

### 3. Configure the Hook

Context7 can be configured in `.claude/hooks/context7_docs/config.json`:

```json
{
  "enabled": true,
  "proactive_enhancement": true,
  "use_natural_language": true,
  "max_libraries": 3,
  "context_window": 10000,
  "topics": {
    "fastapi": ["routing", "middleware", "authentication"],
    "react": ["hooks", "components", "state"],
    "pandas": ["dataframes", "operations", "io"]
  }
}
```

## How It Enhances Code Generation

### Without Context7:
```python
# Claude generates basic FastAPI code
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

### With Context7:
```python
# Claude generates with current best practices
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="My API",
    version="1.0.0",
    docs_url="/api/docs"
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    
@app.get("/", status_code=status.HTTP_200_OK)
async def read_root():
    """Root endpoint with proper status code."""
    return {"status": "healthy"}
```

## Natural Language Enhancement

Context7 can capture intent from user messages:

```
User: "I need to build a REST API with FastAPI that handles user authentication"
```

Context7 detects:
- Library: `fastapi`
- Topic: `authentication`
- Fetches relevant auth documentation

## MCP Communication Flow

1. **User Request**: "Create a FastAPI endpoint"
2. **Claude Prepares Code**: About to write FastAPI imports
3. **Context7 Hook**:
   ```json
   {
     "tool": "resolve-library-id",
     "arguments": {"libraryName": "fastapi"}
   }
   // Returns: "/fastapi/docs"
   
   {
     "tool": "get-library-docs",
     "arguments": {
       "context7CompatibleLibraryID": "/fastapi/docs",
       "topic": "routing",
       "tokens": 10000
     }
   }
   ```
4. **Enhanced Context**: Claude receives documentation
5. **Better Code**: Claude generates with best practices

## Troubleshooting

### "Context7 MCP server not available"
1. Check Claude Desktop config includes Context7
2. Restart Claude Desktop
3. Verify network access to MCP server

### "No documentation returned"
1. Library might not be in Context7 database
2. Check library name spelling
3. Try without topic parameter

### Performance Issues
1. Reduce `max_libraries` to 2
2. Lower `context_window` to 5000
3. Disable `use_natural_language` if not needed

## Advanced Configuration

### Custom Topics
```json
{
  "topics": {
    "your_library": ["specific_topic", "another_topic"]
  }
}
```

### Caching
```json
{
  "cache_duration_hours": 24,
  "cache_directory": ".claude/context7/cache"
}
```

## Integration with TDD-Guard

Context7 and TDD-Guard work together:
1. TDD-Guard ensures tests exist first
2. Context7 provides documentation for implementation
3. Result: Well-tested code following best practices