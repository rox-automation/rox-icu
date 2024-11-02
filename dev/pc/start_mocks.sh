#!/bin/bash

# Kill background processes on Ctrl+C
trap 'kill $(jobs -p)' INT

# Start both processes
icu mock --node-id 1 &
icu mock --node-id 2 &

# Wait for all processes
wait
