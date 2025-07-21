#!/bin/bash

# Start DynamoDB Local in the background
cd /opt/dynamodb
java -Djava.library.path=./DynamoDBLocal_lib -jar DynamoDBLocal.jar -sharedDb &

echo "DynamoDB Local started on port 8000"
echo "To use it, set the following environment variable:"
echo "export DYNAMODB_ENDPOINT_URL=http://localhost:8000"