{ pkgs, common }:

pkgs.mkShell {
  name = "backend";

  packages = common.packages
    ++
    (with pkgs; [
    python313
    uv
  ]);

  shellHook = ''
    echo "==========| Backend Shell |=========="
    echo "Backend environment:"

        python --version
        uv --version
    echo ""
  ''
  +
  common.shellHook
  ;
}
