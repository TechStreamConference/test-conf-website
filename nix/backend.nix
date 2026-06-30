{ pkgs, common }:

pkgs.mkShell {
  name = "backend";

  packages = common.packages
    ++
    (with pkgs; [
    uv
  ]);

  shellHook = ''
    echo "==========| Backend Shell |=========="
    echo "Backend environment:"
    ''
    +
    common.shellHook
    +
    ''
    echo "Specific Backend Versions:"
        uv --version
    echo ""
    echo ""
  ''
  ;
}
