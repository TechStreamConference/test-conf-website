# TECH STREAM CONFERENCE WEBSITE

## Setup

### 1. Install Nix (one-time)

```sh
curl --proto '=https' --tlsv1.2 -fsSL https://install.determinate.systems/nix | sh -s -- install
```

This uses the recommended [Determinate Systems installer](https://install.determinate.systems). You can use another installation method, but make sure your Nix version supports flakes.

### 2. Clone the Repository

```sh
git clone git@github.com:TechStreamConference/test-conf-website.git
cd test-conf-website
```

You can also use the HTTPS URL from the [repository page](https://github.com/TechStreamConference/test-conf-website).

### 3. Enter a Development Shell

```sh
nix develop             # whole project
nix develop .#frontend  # frontend only
nix develop .#backend   # backend only
```

### 4. Install dependencies

Run `just setup` from the relevant directory:

| Directory    | Effect                             |
|--------------|------------------------------------|
| `./`         | Sets up all dependencies           |
| `backend/`   | Sets up only backend dependencies  |
| `frontend/`  | Sets up only frontend dependencies |

```sh
just setup
```

---

### Optional: Automatic shell activation with direnv

[direnv](https://direnv.net) is optional but recommended. It automatically loads the correct Nix development shell when you enter the repository or any of its subdirectories, so you do not need to run `nix develop` manually.

**direnv must be installed on your system outside of the project’s Nix shell.** Follow the [direnv installation guide](https://direnv.net/docs/installation.html) and hook it into your shell.

If you use VS Code, also install a direnv extension (e.g. [mkhl.direnv](https://marketplace.visualstudio.com/items?itemName=mkhl.direnv)).

The repository includes the following `.envrc` files:

**`.envrc`** (repo root):

```envrc
use flake
```

**`backend/.envrc`**:

```envrc
use flake ..#backend
```

**`frontend/.envrc`**:

```envrc
use flake ..#frontend
```

Each `.envrc` must be allowed individually. The `just init-direnv` command does this for all three directories at once. Because `just` is provided by the Nix shell, enter it manually the first time, then run the command:

```sh
nix develop  # Enter Nix shell.
just init-direnv  # Setup direnv.
```

After that, direnv will activate the correct shell automatically whenever you enter the repository or one of its subdirectories.

If you prefer not to use direnv, you can always enter a shell manually with `nix develop`, `nix develop .#frontend`, or `nix develop .#backend`.
