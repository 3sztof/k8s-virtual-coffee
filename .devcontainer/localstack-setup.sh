#!/bin/bash
set -e

# Configure AWS CLI for local development
mkdir -p ~/.aws

# Create credentials file if it doesn't exist
if [ ! -f ~/.aws/credentials ]; then
    cat > ~/.aws/credentials << EOL
[default]
aws_access_key_id = localstack
aws_secret_access_key = localstack
EOL
    echo "Created AWS credentials for local development"
fi

# Create config file if it doesn't exist
if [ ! -f ~/.aws/config ]; then
    cat > ~/.aws/config << EOL
[default]
region = us-east-1
output = json
EOL
    echo "Created AWS config for local development"
fi

echo "AWS CLI configured for local development"

# Set environment variables for DynamoDB local
echo 'export DYNAMODB_ENDPOINT_URL="http://localhost:8000"' >> ~/.bashrc
echo 'export DYNAMODB_ENDPOINT_URL="http://localhost:8000"' >> ~/.zshrc

# Set these variables for the current session too
export DYNAMODB_ENDPOINT_URL="http://localhost:8000"

echo "DynamoDB local environment variables configured"
