---
inclusion: always
---

# Pre-Commit Hooks and Static Code Analysis Rule

## Purpose
This rule ensures that pre-commit hooks are run and static code issues are fixed before committing changes to the repository, maintaining code quality and consistency.

## Guidelines

1. Before committing any changes:
   - Run pre-commit hooks to catch common issues
   - Fix any static code issues identified by linters and formatters
   - Ensure all tests pass for the modified code

2. Pre-commit process:
   ```
   # Run pre-commit hooks on all staged files
   pre-commit run --all-files
   
   # Fix any issues identified
   # Re-stage fixed files
   git add [fixed files]
   ```

3. Common static code issues to check for:
   - Code formatting inconsistencies
   - Unused imports or variables
   - Syntax errors
   - Type checking issues
   - Security vulnerabilities
   - Documentation issues

4. Language-specific checks:
   - Python: flake8, black, isort, mypy
   - JavaScript/TypeScript: ESLint, Prettier
   - Infrastructure as Code: yamllint, cfn-lint, terraform fmt

5. If pre-commit hooks fail:
   - Fix the identified issues
   - Re-run the hooks to verify fixes
   - Only proceed with the commit once all hooks pass

## Integration with Auto-Commit Task Rule

When following the auto-commit task rule:
1. Complete the task implementation
2. Run pre-commit hooks and fix any issues
3. Stage all changes (including fixes from pre-commit)
4. Create the commit with the proper task-based message format

## Example

After completing a task and before committing:
```
# Run pre-commit hooks
pre-commit run --all-files

# Fix any identified issues
black backend/api/services/new_service.py
isort backend/api/services/new_service.py

# Re-stage fixed files
git add backend/api/services/new_service.py

# Now proceed with the task-based commit
git commit -m "Task 3.4: Implement New Service

- Added service class with core functionality
- Implemented error handling and validation
- Added unit tests for the service"
```

## Importance
Following this rule ensures:
- Consistent code style across the project
- Early detection of potential bugs and issues
- Reduced technical debt
- Cleaner code reviews focused on functionality rather than style
- Higher overall code quality