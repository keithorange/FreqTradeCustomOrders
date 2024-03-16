#!/bin/bash

# Command pattern to look for
command_pattern='freqtrade trade'

# Use pgrep to find processes based on the command pattern
pids=$(pgrep -f "$command_pattern")

# Check if any PIDs were found
if [ -z "$pids" ]; then
    echo "No freqtrade processes found."
else
    echo "Killing freqtrade processes with PIDs: $pids"
    # Use pkill to kill the processes based on the same pattern
    pkill -f "$command_pattern"
    echo "Processes killed."
fi
