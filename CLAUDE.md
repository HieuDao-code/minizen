- Always use `uv` instead of `pip` commands`
- Write docstrings for all modules, functions, methods, and classes to explain their purpose and usage.
- Use Google-style docstrings with `Args:`, `Returns:`, and `Raises:` sections where applicable. Omit sections that are not relevant (e.g. no `Returns:` for `-> None`).

## Test Writing Conventions

- Type hints: Always include type hints for all test function parameters (fixtures included).
- Kwargs over args: Prefer keyword arguments when calling functions/constructors under test.
- Mock assertions: Always use `assert_called_once_with(...)` instead of `assert_called_once()` + separate argument checks.
- arrange / act / assert: Structure every test with these three sections, separated by blank lines. Use comments `# arrange`, `# act`, `# assert` to label each section. But avoid verbose description of the steps, as the code should be self-explanatory.
- Avoid module-level constants: Do not define constants at the module level in test files.
- When user mocker.patch, use the **module** notation to patch the function where it is used.
