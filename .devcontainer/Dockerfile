FROM mcr.microsoft.com/vscode/devcontainers/python:0-3.10-bullseye
RUN apt update && apt install -y bluetooth
RUN setcap 'cap_net_raw,cap_net_admin+eip' `which hcitool`
