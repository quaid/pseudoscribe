#!/bin/sh
set -e

echo "Starting Xvfb..."
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
sleep 2

echo "Running extension tests..."
npm test

echo "Tests completed successfully"
