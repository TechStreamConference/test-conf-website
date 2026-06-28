{ pkgs, common }:

pkgs.mkShell {
  name = "frontend";

  packages = common.packages
    ++
    (with pkgs; [
    nodejs_22
    pnpm
  ]);

  shellHook = ''
    echo "==========| Fontend Shell |=========="
    echo "Frontend environment:"
    ''
    +
    common.shellHook
    +
    ''
    echo "Specific Frontend Versions:"
    echo "Node Version:"
        node --version
    echo "pnpm Version:"
        pnpm --version
    echo ""
    echo ""
  ''
  ;
}
