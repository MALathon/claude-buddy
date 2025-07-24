# Run Claude Buddy Test Suite

Execute comprehensive tests for Claude Buddy hooks and components.

## Test Categories Available:
- **Components**: Test individual hook functionality (Post-Tool Linter, TDD-Guard, Context7)
- **Integration**: Test external tool integration and end-to-end workflows  
- **Concurrency**: Test resource management and concurrent operation handling
- **Demos**: Test realistic usage scenarios with actual code examples
- **Scenarios**: Test edge cases and complex real-world situations

## Common Test Commands:
```bash
# Run all tests
python -m pytest src/tests/

# Test specific component
python -m pytest src/tests/components/

# Test external integrations
python -m pytest src/tests/integration/

# Run concurrency tests
python -m pytest src/tests/concurrency/

# Run demonstration tests
python -m pytest src/tests/demos/
```

## Installation Tests:
Test the complete installation and hook integration:
```bash
python src/tests/integration/test_installation_integration.py
```

Use this command to verify Claude Buddy is working correctly in your environment.