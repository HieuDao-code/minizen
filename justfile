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

# Update dependencies, hooks, actions lockfile and nix flake (7-day cooldown)
[group('Project')]
update:
    #!/usr/bin/env bash
    set -euo pipefail
    uv lock --upgrade
    prek update --freeze
    gh actions-lock
    until=$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ)
    sha=$(gh api "repos/NixOS/nixpkgs/commits?sha=nixpkgs-unstable&until=${until}&per_page=1" --jq '.[0].sha')
    nix flake lock --override-input nixpkgs "github:NixOS/nixpkgs/${sha}"

# Run tests
[group('Project')]
test:
    tox
