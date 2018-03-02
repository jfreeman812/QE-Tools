# Add pyenv-related PATHs for discovery
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH:$HOME/.local/bin"
# setup relevant Python versions for tox testing using pyenv if present
if command -v pyenv; then
    eval "$(pyenv init -)"
    pip install tox-pyenv
    pyenv install -s 2.7.13
    pyenv install -s 3.5.4
    pyenv install -s 3.6.4
    pyenv local 3.6.4 3.5.4 2.7.13
fi
