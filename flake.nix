{
  description = "Python dev shell";

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
          just # Handy way to save and run project-specific commands
          pinact # Pin GitHub Actions versions
          uv # Extremely fast Python package installer and resolver
        ];

        shellHook = ''
          if ! uv tool list 2>/dev/null | grep -q '^tox '; then
            uv tool install tox --with tox-uv-bare
          fi
          echo "🐍 $(python --version)"
          exec fish
        '';
      };
    };
}
