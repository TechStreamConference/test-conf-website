FROM ghcr.io/astral-sh/uv:python3.13-trixie AS base
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN echo "alias ll='ls -la'" >> /etc/bash.bashrc

FROM base AS dev
WORKDIR /workspace
RUN apt update && apt install -y --no-install-recommends \
    git \
    bash \
    bash-completion \
    less \
    openssh-client \
    vim \
    nano \
    shfmt \
    && rm -rf /var/lib/apt/lists/*

ENV SHELL=/bin/bash TERM=xterm-256color
RUN usermod -s /bin/bash root

# Append our prompt + completion + colors to the global Bash rc
RUN cat >> /etc/bash.bashrc <<'EOF'

# Enable bash-completion (including git)
if [ -f /usr/share/bash-completion/bash_completion ]; then
  . /usr/share/bash-completion/bash_completion
fi

# Colorize common tools
alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias egrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'

# If not running interactively, don't do anything
case $- in *i*) ;; *) return ;; esac

# Load Git prompt helper if available (Debian/Ubuntu path)
if [ -f /usr/lib/git-core/git-sh-prompt ]; then
  . /usr/lib/git-core/git-sh-prompt
  GIT_PS1_SHOWDIRTYSTATE=1
  GIT_PS1_SHOWUNTRACKEDFILES=1
  GIT_PS1_SHOWUPSTREAM=auto
  _git_branch='\[\e[33m\]$(__git_ps1 " (%s)")\[\e[00m\]'
else
  # Fallback: compute branch with git (slower, only if in a repo)
  _git_branch='$(b=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) && [ -n "$b" ] && printf " \033[33m(%s)\033[0m" "$b")'
fi

# Colored PS1: user@host (green for user, red for root) : path (blue) (branch) $/#
if [ -x /usr/bin/tput ] && tput setaf 1 >/dev/null 2>&1; then
  if [ "$EUID" -eq 0 ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\e[01;31m\]\u@\h\[\e[00m\]:\[\e[01;34m\]\w\[\e[00m\]'"${_git_branch}"'\$ '
  else
    PS1='${debian_chroot:+($debian_chroot)}\[\e[01;32m\]\u@\h\[\e[00m\]:\[\e[01;34m\]\w\[\e[00m\]'"${_git_branch}"'\$ '
  fi
else
  PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi

PROMPT_DIRTRIM=2
unset _git_branch
EOF
COPY dev-entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]


FROM base AS prod_builder
WORKDIR /app
COPY ./backend/ /app/backend
WORKDIR /app/backend
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim AS prod
ENV PATH="/app/backend/.venv/bin:$PATH"
WORKDIR /app/backend
COPY ./backend/src /app/backend/src
COPY --from=prod_builder /app/backend/.venv /app/backend/.venv
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "80"]
