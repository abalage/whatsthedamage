---
applyTo: "**"
---

# Project general coding conventions
- **KISS**: Keep It Simple, Stupid. Avoid over-engineering.
- **DRY**: Don't Repeat Yourself. Reuse code via functions, classes, modules
- **Backward compatibility**: Avoid breaking changes in public APIs. Use deprecation warnings.
- **No Sensitive Data**: Never log or store sensitive data (passwords, personal info, secrets).

# Error Handling
- Use exceptions for error handling. 
- Always log errors with contextual information.

# Python Specific overrides
- Avoid using [Any] type hint unless absolutely necessary.
- For running python code try to use already existing virtual environment.

# Testing
- Prefer parameterized tests to reduce code duplication.
- Use fixtures.
- Maintainability over 100% coverage.