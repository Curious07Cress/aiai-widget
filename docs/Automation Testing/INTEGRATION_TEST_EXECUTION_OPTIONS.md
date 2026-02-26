# Integration Test Execution

## Run Tests Now (SSH)

1. SSH into sandbox:
   ```bash
   ssh user@<sandbox-hostname>
   ```

2. Set credentials:
   ```bash
   export AZURE_OPENAI_API_KEY="<key>"
   export AZURE_OPENAI_ENDPOINT="<endpoint>"
   ```

3. Run tests:
   ```bash
   cd /path/to/ai-assembly-structure
   pytest src/i3dx_aiassistant_asmstruct/skill_classifier/tests/integration/ -v
   ```

## Expected Output

```
107 tests | 93%+ pass rate | ~3 minutes
```

## If Tests Fail

| Error | Fix |
|-------|-----|
| Connection timeout | Check network to Azure OpenAI |
| 401 Unauthorized | Verify API key |
| Module not found | Run `pip install -e ".[test]"` |
