# List all commands
list:
  just --list

# Bump version
[group('Project')]
bump:
    cz bump

# Check code
[group('Project')]
check:
    ruff check
    ruff format --check
    ty check
    zizmor . --persona auditor
    uv audit
    cz check --rev-range origin/main..HEAD

# Start development environment
[group('Project')]
dev:
    nix develop --command fish

# Show docs
[group('Project')]
docs:
    zensical serve --open

# Format code
[group('Project')]
fmt:
    ruff format

# Update dependencies, workflows, pre-commit hooks and nix flake
[group('Project')]
update:
    uv lock --upgrade
    prek auto-update --freeze
    pinact run --update --min-age 7
    nix flake update

# Run tests
[group('Project')]
test:
    tox
