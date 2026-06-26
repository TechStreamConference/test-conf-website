{ pkgs }:

pkgs.mkShell {
  name = "frontend";

  packages = with pkgs; [
    nodejs_22
    pnpm
  ];

  shellHook = ''
    echo "==========| End Fontend Nix Script |=========="
    echo "Frontend environment:"
        node --version
        pnpm --version
    echo ""
  '';
}
