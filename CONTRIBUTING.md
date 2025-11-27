# Contributing to whatsthedamage

Thank you for your interest in improving `whatsthedamage`! We welcome contributions of all kinds—bug fixes, features, documentation, and more.

## How to Contribute

1. **Fork the repository** and create your branch from `main`.
2. **Install dependencies** using the provided Makefile:
   ```sh
   make dev
   ```
3. **Run tests** before and after making changes:
   ```sh
   make test
   # or
   pytest
   ```
4. **Follow project conventions:**
   - Use the MVC structure (see `ARCHITECTURE.md`).
   - Centralize config in `config/config.py`.
   - Never log sensitive data; always validate input.
   - Close file handles promptly.
   - Use English for code/comments; localize user-facing strings with `gettext`.
5. **Document your changes** in code and update relevant docs (`README.md`, `ARCHITECTURE.md`, etc.).
6. **Open a pull request** with a clear description and motivation for your changes.

## Code Style & Practices
- Use PEP8 for Python code formatting.
- Write clear, descriptive commit messages.
- Prefer small, focused PRs over large, sweeping changes.
- Add or update tests for new features and bug fixes.
- Use type hints and docstrings for public functions/classes.

## Reviewing & Merging
- All PRs are reviewed for correctness, clarity, and adherence to project conventions.
- Address review comments promptly.
- Squash commits if requested before merging.

## Reporting Issues
- Use GitHub Issues for bugs, feature requests, and questions.
- Provide clear steps to reproduce, expected vs. actual behavior, and relevant logs/configs.

## Community & Support
- Be respectful and constructive in all communications.
- If you need help, open an issue or join discussions.

---
For more details, see `README.md`, `ARCHITECTURE.md`, and `.github/copilot-instructions.md`.
