{ pkgs }:

pkgs.mkShell {
  name = "backend";

  packages = with pkgs; [
    python313
    uv
  ];

  shellHook = ''
    echo "==========| End Backend Nix Script |=========="
    echo "Backend environment:"
        python --version
        uv --version
    echo ""
  '';
}
