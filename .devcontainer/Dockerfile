FROM mcr.microsoft.com/devcontainers/python:3.11

# Install additional OS packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    zsh \
    curl \
    git \
    jq \
    make \
    vim \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install AWS DynamoDB local
RUN mkdir -p /opt/dynamodb && \
    curl -L https://d1ni2b6xgvw0s0.cloudfront.net/v2.0/dynamodb_local_latest.tar.gz | tar xz -C /opt/dynamodb

# Install Oh My Zsh for better terminal experience
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# Set up Python environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create a non-root user with sudo access
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user and add to sudo group
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set the default user
USER $USERNAME

# Set up Python development tools
RUN pip install --user --upgrade pip \
    && pip install --user black isort flake8 mypy pytest pytest-cov

# Set up working directory
WORKDIR /workspace

# Add local bin to PATH
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# Set default shell to zsh
ENV SHELL=/bin/zsh