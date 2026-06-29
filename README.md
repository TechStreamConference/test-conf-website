# TECH STREAM CONFERENCE WEBSITE

## Setup
#### Install Nix (one-time)
```sh
curl --proto '=https' --tlsv1.2 -fsSL https://install.determinate.systems/nix | sh -s -- install
```
- Note: This is the recomended way. You can install it as you want. Make sure, that youre Nix version can handle this project.
#### clone repo
```sh
git clone git@github.com:TechStreamConference/test-conf-website.git
```
- Note: You can copy the SSH or HTTPS Link [here](https://github.com/TechStreamConference/test-conf-website)
#### move into repo
```sh
cd test-conf-website
```
- Note: When you did rename the repo, you have to replace the name within the previous command.
#### install with nix
```sh
nix develop             (whole project)
nix develop .#frontend  (just frontend)
nix develop .#backend   (just backend)
```
#### setup dependencies
```sh
just setup
```

- Note: This command can be executed within multiple directories:
    - `root`: setups all dependencies
    - `/backend`: setups only backend dependencies
    - `/frontend`: setups only frontend dependencies
