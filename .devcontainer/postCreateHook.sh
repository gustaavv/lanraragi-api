#!/bin/bash

# code is not available at this stage because it is still in the container creation phase
# a workaround, see:
# https://github.com/microsoft/vscode-remote-release/issues/8535#issuecomment-1825413099
# note that the path to code-server has changed
code="$(ls ~/.vscode-remote/bin/*/bin/code-server* | head -n 1)"

# remove useless extensions bundled with ms-python.python
$code --install-extension ms-python.python
$code --uninstall-extension ms-python.debugpy --uninstall-extension ms-python.vscode-python-envs

make install