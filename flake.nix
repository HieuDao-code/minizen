{
  description = "🐍";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          gh # GitHub CLI, used for gh actions-lock
          just # Handy way to save and run project-specific commands
          uv # Extremely fast Python package installer and resolver
        ];

        shellHook = ''
          if ! gh extension list 2>/dev/null | grep -q "gh-actions-lock.*v0.4.1"; then
            gh extension install github/gh-actions-lock --pin v0.4.1 --force
          fi

          if ! uv tool list 2>/dev/null | grep -q '^tox '; then
            uv tool install tox --with tox-uv-bare
          fi
        '';
      };
    };
}
