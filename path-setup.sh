# Add pyenv-related PATHs for discovery
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PATH:$PYENV_ROOT/bin:$HOME/.local/bin"

# For CICD we need to have the PYENV_ROOT where we just put it,
# not where "pyenv init -" will, so save our PATH now...
SAVED_PATH=$PATH

# setup relevant Python versions for tox testing using pyenv if present
if command -v pyenv; then
    eval "$(pyenv init -)"
    # ...and undo what "pyenv init -" did for setting PATH
    export PATH=$SAVED_PATH
    pip install tox-pyenv
    pyenv install -s 2.7.13
    pyenv install -s 3.5.4
    pyenv install -s 3.6.4
    pyenv install -s 3.7.0
    pyenv local 3.7.0 3.6.4 3.5.4 2.7.13
fi
