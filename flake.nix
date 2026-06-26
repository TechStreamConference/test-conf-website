{
  description = "TECH STREAM CONFERENCE Website | uv and NodeJS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        backend = import ./nix/backend.nix { inherit pkgs; };
        frontend = import ./nix/frontend.nix { inherit pkgs; };

      in {
        devShells = {

          inherit backend frontend;

          default = pkgs.mkShell {
            name = "fullstack";

            inputsFrom = [
              backend
              frontend
            ];

            shellHook = ''
    echo ""
    echo "==========| End Global Nix Script |=========="
    echo "Development environment ready"
    echo "Frontend: pnpm"
    echo "Backend : uv"
    echo ""
    echo "Available commands:"
    echo "  commands are to come"
    echo "============================================="
    echo ""
  '';
          };
        };
      });
}
