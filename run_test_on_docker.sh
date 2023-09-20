#!/bin/bash

# Check if the required arguments are provided
if [ "$#" -ne 7 ]; then
  echo "Usage: $0 <docker-container-name> <concurrent_requests> <duration_seconds> <test_unique_name> <test_display_name> <test_description> <endpoint_url>"
  exit 1
fi

DOCKER_CONTAINER_NAME=$1
CONCURRENT_REQUESTS=$2
DURATION_SECONDS=$3
TEST_UNIQUE_NAME=$4
TEST_DISPLAY_NAME=$5
TEST_DESCRIPTION=$6
SERVER_URL=$7
docker exec -it $DOCKER_CONTAINER_NAME go test -args "$CONCURRENT_REQUESTS" "$DURATION_SECONDS" "$TEST_UNIQUE_NAME" "$TEST_DISPLAY_NAME" "$TEST_DESCRIPTION" "$SERVER_URL"
