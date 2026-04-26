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
    nix develop -c fish

# Show docs
[group('Project')]
docs:
    zensical serve --open

# Format code
[group('Project')]
fmt:
    ruff format

# Run main script
[group('Project')]
run:
    python main.py

# Update dependencies, workflows, pre-commit hooks and nix flake
[group('Project')]
update:
    uv lock --upgrade --exclude-newer "1 week"
    prek auto-update --freeze --cooldown-days 7
    pinact run --update --min-age 7
    nix flake update

# Run tests
[group('Project')]
test:
    tox
