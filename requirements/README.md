# Requirements Structure

This directory contains the project's Python package requirements, organized by environment:

- `base.txt`: Core requirements needed in all environments
- `dev.txt`: Development environment requirements
- `prod.txt`: Production environment requirements
- `test.txt`: Testing environment requirements

## Installation

For development:
```bash
pip install -r requirements/dev.txt
```

For production:
```bash
pip install -r requirements/prod.txt
```

For testing:
```bash
pip install -r requirements/test.txt
```

## Requirements Management

- Always add new packages to the appropriate requirements file
- Specify exact versions using `==` to ensure consistency
- Use `-r base.txt` to include base requirements in other files
- Keep requirements organized by category with comments 