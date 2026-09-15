#!/bin/bash

# remove useless extensions bundled with ms-python.python
code --uninstall-extension ms-python.debugpy --uninstall-extension ms-python.vscode-python-envs

make install