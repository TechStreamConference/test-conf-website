{ pkgs }:

{
  packages = with pkgs; [
    git
    just
  ];

  shellHook = ''
    echo "Common Versions:"
        git --version
        just --version
    echo ""
  '';
}

