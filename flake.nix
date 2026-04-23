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
          prek # Better `pre-commit`
          python314Packages.tox # Generic virtualenv management and test command line tool
          uv # Extremely fast Python package installer and resolver
        ];

        shellHook = ''
          echo "🐍 $(python --version)"
          exec fish
        '';
      };
    };
}
