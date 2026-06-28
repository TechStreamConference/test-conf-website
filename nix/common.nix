{ pkgs }:

{
  packages = with pkgs; [
    git
    just
  ];

  shellHook = ''
    echo "common versions"
        git --version
        just --version
  '';
}

