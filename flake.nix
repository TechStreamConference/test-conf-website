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

        common = import ./nix/common.nix {
          inherit pkgs;
        };

        backend = import ./nix/backend.nix {
           inherit pkgs common; 
        };
        frontend = import ./nix/frontend.nix { 
          inherit pkgs common; 
        };

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
    echo "'just' for availabe commands."
    echo "Note: This may vary within different directories."
    echo "============================================="
    echo ""
  '';
          };
        };
      });
}
