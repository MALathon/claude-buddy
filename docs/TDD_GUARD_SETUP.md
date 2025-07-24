# TDD-Guard Setup for Your Project

## How TDD-Guard Works

When Claude Buddy is installed and TDD-Guard is enabled, it enforces test-driven development by:

1. **Checking for test results** before allowing code changes
2. **Looking in your project's** `.claude/tdd-guard/data/` directory
3. **Blocking implementation** if tests don't exist or are failing

## Directory Structure

TDD-Guard expects this structure in YOUR project (not in Claude Buddy):

```
Your-Project/
├── .claude/
│   └── tdd-guard/
│       └── data/
│           ├── test.json         # Test results from your test runner
│           ├── modifications.json # Tracks code changes
│           └── todos.json        # Task tracking
├── src/
│   └── your_code.py
└── tests/
    └── test_your_code.py
```

## Setting Up Test Reporters

### For pytest (Python)

1. Install the pytest JSON reporter:
```bash
pip install pytest-json-report
```

2. Create a pytest configuration that outputs to the correct location:

```bash
# Run tests with JSON output
pytest --json-report-file=.claude/tdd-guard/data/test.json
```

Or add to `pytest.ini`:
```ini
[tool.pytest.ini_options]
addopts = --json-report-file=.claude/tdd-guard/data/test.json
```

### For vitest (JavaScript/TypeScript)

1. Configure vitest to output JSON results:

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

### For Jest

```javascript
// jest.config.js
module.exports = {
  reporters: [
    'default',
    ['jest-json-reporter', {
      outputPath: '.claude/tdd-guard/data/test.json'
    }]
  ]
}
```

## Test Result Format

TDD-Guard expects test results in this format:

```json
{
  "testModules": [{
    "moduleId": "test_file.py",
    "tests": [{
      "name": "test_function_name",
      "status": "passed",  // or "failed", "skipped"
      "duration": 0.123
    }]
  }],
  "summary": {
    "total": 10,
    "passed": 8,
    "failed": 2,
    "skipped": 0
  }
}
```

## Workflow Example

1. **Write a test first** (Red phase):
```python
# tests/test_calculator.py
def test_add():
    from calculator import add
    assert add(2, 3) == 5  # This will fail
```

2. **Run tests** to generate `.claude/tdd-guard/data/test.json`:
```bash
pytest --json-report-file=.claude/tdd-guard/data/test.json
```

3. **Try to implement** - TDD-Guard will block if tests are failing:
```python
# calculator.py
def add(a, b):
    return a + b  # Only allowed after test exists
```

4. **Run tests again** - now they pass
5. **Implementation is allowed** (Green phase)

## Configuration

TDD-Guard can be configured via environment variables:

```bash
export TDD_GUARD_STRICT=true         # Enforce strict TDD
export TDD_GUARD_MODEL=claude        # Use Claude for validation
export TDD_GUARD_TEST_RUNNER=pytest  # Specify test runner
```

## Troubleshooting

1. **"No test results found"**: Ensure your test runner outputs to `.claude/tdd-guard/data/test.json`
2. **Tests not detected**: Check the JSON format matches the expected schema
3. **Permission issues**: Ensure `.claude/tdd-guard/data/` directory exists and is writable

## Integration with CI/CD

Add to your CI pipeline:

```yaml
# GitHub Actions example
- name: Run tests with TDD-Guard format
  run: |
    mkdir -p .claude/tdd-guard/data
    pytest --json-report-file=.claude/tdd-guard/data/test.json
```

This ensures TDD-Guard has test results available during development.