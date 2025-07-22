# Use minimal base image
FROM mcr.microsoft.com/devcontainers/base:debian-12

# Install only git
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    git \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /workspace

# Comment: Other dependencies like Python, Node.js, and AWS CLI are removed
# They can be reinstated later when needed
