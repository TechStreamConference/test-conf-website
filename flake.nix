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
            name = "root";

            packages = common.packages;

            shellHook = common.shellHook + ''
    echo ""
    echo "==========| Root Shell |=========="
    echo "Development environment ready"
    echo ""
    echo "'just' for available commands."
    echo "Note: Enter backend/ or frontend/ for their respective tools."
    echo "============================================="
    echo ""
  '';
          };
        };
      });
}
