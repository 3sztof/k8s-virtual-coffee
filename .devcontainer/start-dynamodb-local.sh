#!/bin/bash
# DISABLED DYNAMODB LOCAL SETUP
# This script is currently disabled as per user request to have a minimal git-only container

# ====================================================================
# INSTRUCTIONS FOR FUTURE REFERENCE WHEN DYNAMODB FUNCTIONALITY IS NEEDED:
# ====================================================================
#
# # To run DynamoDB locally, you can use the following commands:
# 1. Install AWS CLI in the container: 
#    apt-get update && apt-get install -y awscli
#
# 2. Start DynamoDB local with Docker:
#    docker run -p 8000:8000 amazon/dynamodb-local
#
# 3. Create required tables:
#    - Users table: 
#      aws dynamodb create-table --table-name users --attribute-definitions AttributeName=user_id,AttributeType=S --key-schema AttributeName=user_id,KeyType=HASH --billing-mode PAY_PER_REQUEST --endpoint-url http://localhost:8000
#    - Matches table:
#      aws dynamodb create-table --table-name matches --attribute-definitions AttributeName=match_id,AttributeType=S --key-schema AttributeName=match_id,KeyType=HASH --billing-mode PAY_PER_REQUEST --endpoint-url http://localhost:8000
#    - Config table:
#      aws dynamodb create-table --table-name config --attribute-definitions AttributeName=config_name,AttributeType=S --key-schema AttributeName=config_name,KeyType=HASH --billing-mode PAY_PER_REQUEST --endpoint-url http://localhost:8000
#
# ====================================================================
# To re-enable this script, uncomment the executable code and update 
# the devcontainer.json to include the required extensions and dependencies
# ====================================================================

echo "DynamoDB Local setup is currently disabled."
echo "This container is configured for git operations only."
echo "To enable DynamoDB functionality, see the instructions in this file."
