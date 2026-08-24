{
  description = "TECH STREAM CONFERENCE Website | uv and NodeJS";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";
    flake-utils.url = "github:numtide/flake-utils";
    git-hooks.url = "github:cachix/git-hooks.nix";
    git-hooks.inputs.nixpkgs.follows = "nixpkgs";
  };

  outputs = { self, nixpkgs, flake-utils, git-hooks }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };
        pre-commit-check = git-hooks.lib.${system}.run {
          src = ./.;
          package = pkgs.prek;
          hooks = {
            ruff-format = {
              enable = true;
              name = "ruff format";
              entry = "uv run --project backend ruff format";
              files = "^backend/.*\\.py$";
              language = "system";
              before = [ "ruff-check" ];
            };
            ruff-check = {
              enable = true;
              name = "ruff check";
              entry = "uv run --project backend ruff check --fix";
              files = "^backend/.*\\.py$";
              language = "system";
            };
          };
        };
      in {
        checks.pre-commit-check = pre-commit-check;

        devShells.default = pkgs.mkShell {
          name = "dev";

          packages = with pkgs; [
            git
            just
            just-lsp
            nodejs_22
            pnpm
            uv
          ] ++ pre-commit-check.enabledPackages;

          shellHook = pre-commit-check.shellHook + ''
            echo ""
            echo "==========| Dev Shell |=========="
            echo "Development environment ready"
            echo ""
            git --version
            just --version
            just-lsp --version
            echo "node version $(node --version)"
            echo "pnpm version $(pnpm --version)"
            uv --version
            echo ""
            echo "'just' for available commands."
            echo "================================="
            echo ""
          '';
        };
      });
}
