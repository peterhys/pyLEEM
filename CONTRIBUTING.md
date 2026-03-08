# Contributing

Thank you for your interest in contributing to PyLEEM!
This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Create a new branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Install Development Dependencies

Using pip:
```bash
pip install -e ".[test]"
```

### Running Tests

Run the full test suite with tox:
```bash
tox
```

## Code Style Guidelines

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use Black for code formatting before submission
- Maximum line length: 88 characters (Black default)

### Documentation Style

- Add docstrings to all public classes, methods, and functions
- Use reStructuredText format for docstrings
- Include parameter types, return types, and examples where helpful


## Contribute

### Bug Reports

If you find a bug:

1. Check if it's already reported in [Issues](https://github.com/peterhys/PyLEEM/issues)
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs. actual behavior
   - Python version and package versions
   - Minimal code example if possible

### Feature Requests

For new features:

1. Open an issue first to discuss the feature
2. Explain the use case and benefits
3. Wait for maintainer feedback before implementing

### Pull Requests

#### Before Submitting

- [ ] Code follows project style guidelines
- [ ] All tests pass (`pytest`)
- [ ] New tests added for new functionality
- [ ] Documentation updated (docstrings, README, etc.)

#### Submitting a PR

1. Push your branch to your fork
2. Open a Pull Request against the `develop` branch
3. Fill out the PR template
4. Link any related issues
5. Wait for review

#### PR Review Process

- Maintainers will review your code
- Address any requested changes
- Once approved, your PR will be merged

## Branching Strategy

- `main` - Stable releases only
- `develop` - Development branch (submit PRs here)
- `feature/*` - New features
- `fix/*` - Bug fixes
- `docs/*` - Documentation updates


## Questions?

- Open a [Discussion](https://github.com/peterhys/PyLEEM/discussions)
- Check existing [Issues](https://github.com/peterhys/PyLEEM/issues)

## Code of Conduct

This project adheres to a Code of Conduct. 
By participating, you are expected to uphold this code.
Please report unacceptable behavior to the maintainer.

## License

By contributing to PyLEEM, you agree that your contributions
will be licensed under the GNU General Public License v3.0.

---

Thank you for contributing to PyLEEM! Your contributions help
make scientific software better for everyone.
