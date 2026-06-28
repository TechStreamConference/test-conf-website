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
    echo "Node version:"
        node --version
    echo "pnpm version:"
        pnpm --version
    echo ""
  ''
  +
  common.shellHook
  ;
}
