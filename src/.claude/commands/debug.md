# Claude Buddy Debug Mode

Enable detailed logging and debugging for Claude Buddy hooks.

## Debug Features:
- **Real-time log streaming**: Watch hook activity as it happens
- **Detailed operation tracking**: See operation IDs and resource usage
- **External tool diagnostics**: Check MCP servers and external dependencies
- **Concurrency monitoring**: Track resource pools and lock contention
- **Performance metrics**: Monitor hook execution times and bottlenecks

## Quick Debug Commands:

### View Recent Logs:
```bash
tail -f .claude/claude_buddy/logs/claude_buddy_$(date +%Y-%m-%d).log
```

### Enable Debug Mode:
Edit hook config files and set `"debug": true`:
- `.claude/claude_buddy/hooks/post_tool_linter/config.json`
- `.claude/claude_buddy/hooks/tdd_guard/config.json`
- `.claude/claude_buddy/hooks/context7_docs/config.json`
- `.claude/claude_buddy/tools/concurrency/config.json`

### Check Hook Status:
```bash
python .claude/claude_buddy/hooks/external_loader.py
```

### Test Individual Components:
```bash
# Test Post-Tool Linter
python .claude/claude_buddy/hooks/post_tool_linter/hook.py

# Test TDD-Guard integration
python .claude/claude_buddy/hooks/tdd_guard/hook.py

# Test Context7 MCP connection
python .claude/claude_buddy/hooks/context7_docs/hook.py
```

## Environment Variables:
Customize timeouts for debugging:
```bash
export CLAUDE_AGENT_TIMEOUT_SECONDS=600
export TDD_GUARD_TIMEOUT_SECONDS=300
export MCP_CALL_TIMEOUT_SECONDS=30
```

Use this command when hooks aren't working as expected or you need detailed execution visibility.