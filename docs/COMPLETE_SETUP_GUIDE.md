# Complete Claude Buddy Setup Guide

## Quick Start

```bash
# 1. Clone and install Claude Buddy
git clone https://github.com/yourusername/claude_buddy.git
cd claude_buddy
./install.sh

# 2. In YOUR project, set up test reporters
cd /path/to/your/project
python /path/to/claude_buddy/scripts/setup_test_reporters.py
```

## What Gets Set Up Automatically

### ✅ Automatic Setup (via install.sh)
1. **Python virtual environment** in `src/.venv`
2. **TDD-Guard** installed locally in `src/node_modules`
3. **Context7 MCP server** configured (if Claude CLI is available)
4. **All Python dependencies** installed

### ❌ Manual Setup Required
1. **Test reporters** - Your test runner needs to output to `.claude/tdd-guard/data/test.json`
2. **Hook configuration** - Enable/disable specific hooks
3. **Project integration** - Copy necessary files to your project

## Step-by-Step Setup

### 1. Install Claude Buddy

```bash
git clone https://github.com/yourusername/claude_buddy.git
cd claude_buddy
./install.sh
```

### 2. Configure Your Project's Test Runner

#### Option A: Automatic Configuration
```bash
cd /your/project
python /path/to/claude_buddy/scripts/setup_test_reporters.py
```

This script will:
- Detect pytest/vitest/jest
- Install necessary reporters
- Configure them to output to `.claude/tdd-guard/data/test.json`
- Create helper scripts in `.claude/tdd-guard/`

#### Option B: Manual Configuration

**For pytest:**
```ini
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
addopts = --json-report-file=.claude/tdd-guard/data/test.json
```

**For vitest:**
```javascript
// vitest.config.js
export default {
  test: {
    reporters: ['default', 'json'],
    outputFile: {
      json: '.claude/tdd-guard/data/test.json'
    }
  }
}
```

**For jest:**
```json
// package.json or jest.config.js
{
  "jest": {
    "reporters": [
      "default",
      ["jest-json-reporter", {
        "outputPath": ".claude/tdd-guard/data/test.json"
      }]
    ]
  }
}
```

### 3. Create Project Structure

In your project root:
```bash
mkdir -p .claude/tdd-guard/data
mkdir -p .claude/hooks
```

### 4. Configure Hooks

Create `.claude/hooks/config.json`:
```json
{
  "tdd_guard": {
    "enabled": true,
    "strict_mode": true
  },
  "context7_docs": {
    "enabled": true,
    "proactive_enhancement": true
  },
  "post_tool_linter": {
    "enabled": true
  }
}
```

### 5. Run Tests to Initialize

```bash
# Run your tests to generate the initial test.json
pytest  # or npm test, or vitest run
```

## How It Works

### TDD-Guard Flow
1. You ask Claude to write code
2. TDD-Guard checks `.claude/tdd-guard/data/test.json`
3. If no tests exist or tests are failing → blocks implementation
4. You write tests first
5. Run tests (they fail - Red phase)
6. Now Claude can implement (Green phase)
7. Tests pass, you can refactor

### Context7 Flow
1. You ask Claude to write code
2. Claude prepares imports/code
3. Context7 detects libraries (fastapi, react, etc.)
4. Fetches current documentation via MCP
5. Claude generates better code with best practices

## Verifying Setup

### Check TDD-Guard
```bash
# In your project
echo '{"event_type":"PreToolUse","tool_name":"Write"}' | \
  /path/to/claude_buddy/src/node_modules/.bin/tdd-guard
```

### Check Context7
```bash
# With Claude CLI
claude mcp list | grep context7
```

### Run Test Reporter
```bash
# Check if test.json is created
.claude/tdd-guard/run-tests.sh
ls -la .claude/tdd-guard/data/test.json
```

## Common Issues

### "No test results found"
- Ensure test runner outputs to `.claude/tdd-guard/data/test.json`
- Run `setup_test_reporters.py` script
- Check file permissions

### "Context7 not available"
- Install Claude CLI: `brew install claude`
- Run: `claude mcp add --transport http context7 https://mcp.context7.com/mcp`
- Restart Claude

### "TDD-Guard not enforcing"
- Check hook is enabled in `.claude/hooks/config.json`
- Verify test.json format matches expected schema
- Ensure TDD-Guard binary is executable

## Advanced Configuration

### Custom Test Locations
```bash
# Set environment variable
export TDD_GUARD_TEST_FILE="/custom/path/test.json"
```

### Strict Mode
```json
{
  "tdd_guard": {
    "strict_mode": true,  // Require ALL tests to pass
    "model": "claude",    // Use Claude for validation
    "timeout": 30         // Seconds to wait
  }
}
```

### Context7 Topics
```json
{
  "context7_docs": {
    "topics": {
      "fastapi": ["routing", "authentication"],
      "react": ["hooks", "performance"]
    }
  }
}
```

## Integration with CI/CD

### GitHub Actions
```yaml
- name: Setup Claude Buddy
  run: |
    mkdir -p .claude/tdd-guard/data
    
- name: Run Tests with TDD-Guard format
  run: |
    pytest --json-report-file=.claude/tdd-guard/data/test.json
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
pytest --json-report-file=.claude/tdd-guard/data/test.json
if [ $? -ne 0 ]; then
  echo "Tests must pass before commit (TDD enforced)"
  exit 1
fi
```

## Best Practices

1. **Always run test setup script** in new projects
2. **Commit `.claude/` directory** to share TDD configuration
3. **Use watch mode** for continuous TDD: `.claude/tdd-guard/watch-tests.sh`
4. **Configure CI** to generate test.json for consistency
5. **Enable strict mode** for maximum TDD enforcement

## Uninstall

To remove Claude Buddy from a project:
```bash
rm -rf .claude/
# Remove test reporter configuration from pytest.ini/package.json/etc.
```