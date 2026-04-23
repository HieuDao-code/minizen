# Python project Template

This is a template repository for python projects.

To get started:

1. Create a repository on GitHub using this template.
2. Enable GitHub Actions in your repository in `.github/workflows`
   - Setup [commitizen](https://commitizen-tools.github.io/commitizen/tutorials/github_actions/#automatic-version-bumping) for version and changelog generation
   - Setup [zensical](https://zensical.org/docs/publish-your-site/) for documentation hosting
   - Setup [renovate](https://docs.renovatebot.com/getting-started/installing-onboarding/) for dependency updates
3. Enable [nix devshells](https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-develop) for development environment setup with `nix develop`
4. Enable [pre-commit](https://pre-commit.com/) with `prek install`
