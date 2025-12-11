#!/bin/bash

# Stop execution if any command fails
set -e

echo "Stopping running containers..."
docker compose down

echo "Pulling latest code from Git..."
git pull

echo "Building Docker images..."
docker compose build

echo "Starting containers..."
docker compose up -d --remove-orphans --scale app=3

echo "Deployment complete!"
