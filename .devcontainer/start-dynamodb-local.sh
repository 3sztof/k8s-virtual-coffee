#!/bin/bash
set -e

# Default values
DYNAMODB_PORT=8000
DATA_DIR="/workspace/.dynamodb-local"
CONTAINER_NAME="k8s-virtual-coffee-dynamodb-local"

# Create data directory if it doesn't exist
mkdir -p $DATA_DIR

# Check if the container is already running
if docker ps -q --filter "name=$CONTAINER_NAME" | grep -q .; then
    echo "DynamoDB Local is already running on port $DYNAMODB_PORT"
else
    # Check if container exists but is stopped
    if docker ps -aq --filter "name=$CONTAINER_NAME" | grep -q .; then
        echo "Starting existing DynamoDB Local container"
        docker start $CONTAINER_NAME
    else
        echo "Creating and starting new DynamoDB Local container"
        docker run -d \
            --name $CONTAINER_NAME \
            -p $DYNAMODB_PORT:8000 \
            -v $DATA_DIR:/data \
            amazon/dynamodb-local \
            -jar DynamoDBLocal.jar -sharedDb -dbPath /data
    fi
    
    echo "DynamoDB Local started on port $DYNAMODB_PORT"
fi

# Wait for DynamoDB to be ready
echo "Waiting for DynamoDB Local to be ready..."
max_attempts=30
attempt=1

while ! curl -s http://localhost:$DYNAMODB_PORT/shell > /dev/null; do
    if [ $attempt -gt $max_attempts ]; then
        echo "DynamoDB Local failed to start after $max_attempts attempts."
        exit 1
    fi
    echo "Waiting for DynamoDB Local to start (attempt $attempt/$max_attempts)..."
    sleep 1
    attempt=$((attempt+1))
done

echo "DynamoDB Local is ready at http://localhost:$DYNAMODB_PORT"

# Create default tables if they don't exist
echo "Checking and creating default tables if needed..."

# List of tables to create with their key schemas
# Format: table_name:partition_key[:sort_key]
TABLES=(
    "users:user_id"
    "matches:match_id"
    "config:config_name"
)

for table_info in "${TABLES[@]}"; do
    IFS=':' read -r table_name partition_key sort_key <<< "$table_info"
    
    # Check if table exists
    if aws dynamodb describe-table --table-name $table_name --endpoint-url http://localhost:$DYNAMODB_PORT 2>/dev/null; then
        echo "Table $table_name already exists"
    else
        echo "Creating table $table_name"
        
        # Build key schema based on whether a sort key is provided
        if [ -z "$sort_key" ]; then
            # Only partition key
            aws dynamodb create-table \
                --table-name $table_name \
                --attribute-definitions AttributeName=$partition_key,AttributeType=S \
                --key-schema AttributeName=$partition_key,KeyType=HASH \
                --billing-mode PAY_PER_REQUEST \
                --endpoint-url http://localhost:$DYNAMODB_PORT
        else
            # Partition key and sort key
            aws dynamodb create-table \
                --table-name $table_name \
                --attribute-definitions \
                    AttributeName=$partition_key,AttributeType=S \
                    AttributeName=$sort_key,AttributeType=S \
                --key-schema \
                    AttributeName=$partition_key,KeyType=HASH \
                    AttributeName=$sort_key,KeyType=RANGE \
                --billing-mode PAY_PER_REQUEST \
                --endpoint-url http://localhost:$DYNAMODB_PORT
        fi
        
        echo "Table $table_name created successfully"
    fi
done

echo "DynamoDB Local setup complete"
