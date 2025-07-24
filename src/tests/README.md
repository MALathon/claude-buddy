# Claude Buddy Test Suite

This directory contains all tests for Claude Buddy, organized by category and purpose.

## 📁 Directory Structure

```
src/tests/
├── README.md                 # This file
├── __init__.py              # Test package init
├── demos/                   # Interactive demonstrations
├── integration/             # Integration and end-to-end tests
├── components/              # Component-specific tests
├── concurrency/             # Concurrency and performance tests
└── scenarios/               # Real-world usage scenarios
```

## 🎭 Test Categories

### 📺 Demos (`demos/`)
Interactive demonstrations showing Claude Buddy features:

- **`test_post_linter_demo.py`** - Post-Tool Linter concurrency demo with before/after code fixing
- **`test_context7_demo.py`** - Context7 documentation enhancement comparison
- **`test_tdd_guard_demo.py`** - TDD-Guard test enforcement demonstration
- **`test_unified_logging_demo.py`** - Unified logging system showcase

**Run demos:**
```bash
python src/tests/demos/test_post_linter_demo.py
python src/tests/demos/test_context7_demo.py
python src/tests/demos/test_tdd_guard_demo.py
python src/tests/demos/test_unified_logging_demo.py
```

### 🔧 Integration Tests (`integration/`)
End-to-end functionality and system integration:

- **`test_context7_integration.py`** - Context7 MCP server integration
- **`test_post_tool_linter_real.py`** - Real Claude CLI integration
- **`test_real_claude_autofix.py`** - Claude agent autofix validation
- **`test_mcp_simple.py`** - Basic MCP protocol testing
- **`test_agent_integration.py`** - Agent system integration
- **`test_end_to_end.py`** - Complete workflow testing
- **`test_external_loader_comprehensive.py`** - External tool loading
- **`test_hook_manager_comprehensive.py`** - Hook management system
- **`test_installation_integration.py`** - Installation process validation
- **`test_integration.py`** - General integration tests
- **`test_registry_integration.py`** - Hook registry functionality

### 📦 Component Tests (`components/`)
Individual component functionality:

- **`test_hooks_comprehensive.py`** - Comprehensive hook testing
- **`test_hooks_intended_use.py`** - Hook usage pattern validation

### ⚡ Concurrency Tests (`concurrency/`)
Performance and concurrent operation testing:

- **`test_concurrency_blocking.py`** - Resource blocking behavior
- **`test_concurrency_waiting.py`** - Resource waiting mechanisms
- **`test_waiting_behavior.py`** - Concurrency wait validation

### 🌍 Scenario Tests (`scenarios/`)
Real-world usage patterns and edge cases:

- **`test_context7_scenarios.py`** - Context7 usage scenarios
- **`test_tdd_guard_scenarios.py`** - TDD-Guard workflow scenarios
- **`test_hooks_real_world.py`** - Real-world hook interactions

## 🚀 Running Tests

### Run All Tests
```bash
# From project root
python -m pytest src/tests/ -v
```

### Run Specific Category
```bash
# Integration tests only
python -m pytest src/tests/integration/ -v

# Component tests only
python -m pytest src/tests/components/ -v

# Concurrency tests only
python -m pytest src/tests/concurrency/ -v
```

### Run Individual Test File
```bash
# Specific test file
python -m pytest src/tests/integration/test_end_to_end.py -v

# Or run directly
python src/tests/demos/test_post_linter_demo.py
```

### Run with Coverage
```bash
python -m pytest src/tests/ --cov=src/hooks --cov-report=html
```

## 🎯 Test Purposes

| Category | Purpose | Coverage |
|----------|---------|----------|
| **Demos** | User-facing demonstrations | Feature showcases |
| **Integration** | System-level functionality | End-to-end workflows |
| **Components** | Individual unit testing | Hook implementations |
| **Concurrency** | Performance validation | Multi-threading behavior |
| **Scenarios** | Edge case coverage | Real-world usage |

## 📊 Test Results

All tests should verify:
- ✅ No mocking - real external tool integration
- ✅ Proper concurrency management 
- ✅ Actual Claude CLI interactions
- ✅ MCP protocol compliance
- ✅ Error handling and recovery
- ✅ Resource cleanup and management

## 🔍 Debugging Tests

### Enable Debug Logging
Set debug mode in hook configs:
```json
{
  "settings": {
    "debug": true
  }
}
```

### View Test Logs
```bash
# Real-time unified logs
tail -f logs/claude_buddy_$(date +%Y-%m-%d).log

# Component-specific logs
tail -f logs/post_tool_linter/$(date +%Y-%m-%d).log
tail -f logs/context7/$(date +%Y-%m-%d).log
tail -f logs/tdd_guard/$(date +%Y-%m-%d).log
```

### Test Environment
Tests use real external tools when available:
- Claude CLI (requires proper installation)
- TDD-Guard npm package
- Context7 MCP server
- Python linters (black, flake8, mypy)

## 📝 Adding New Tests

1. **Choose appropriate category** based on test purpose
2. **Follow naming convention**: `test_[feature]_[type].py`
3. **Include docstrings** explaining test purpose
4. **Use real implementations** - avoid mocking when possible
5. **Add to this README** with description

## 🛠️ Test Dependencies

Required for full test suite:
```bash
pip install pytest pytest-cov
npm install -g @upstash/context7-mcp
npm install -g tdd-guard  # or local installation
```

## 🎪 Contributing

When adding tests:
1. Ensure they demonstrate real functionality
2. Include both positive and negative test cases
3. Document expected behavior clearly
4. Verify tests pass in clean environment
5. Update this README with new test descriptions