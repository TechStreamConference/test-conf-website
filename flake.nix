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
      in {
        devShells.default = pkgs.mkShell {
          name = "dev";

          packages = with pkgs; [
            git
            just
            nodejs_22
            pnpm
            uv
          ];

          shellHook = ''
            echo ""
            echo "==========| Dev Shell |=========="
            echo "Development environment ready"
            echo ""
            git --version
            just --version
            node --version
            pnpm --version
            uv --version
            echo ""
            echo "'just' for available commands."
            echo "================================="
            echo ""
          '';
        };
      });
}
