#!/bin/bash
# Wait for Plasma to fully initialize
# (OTA Update Test)
sleep 3

# Get the connected output name (e.g. Virtual-1 or XWAYLAND0)
OUTPUT=$(kscreen-doctor -o | grep -oP '^Output: \d+ \K\S+' | head -n 1)

if [ -n "$OUTPUT" ]; then
    # Force the resolution to 1920x1080 at 60Hz
    kscreen-doctor output.$OUTPUT.mode.1920x1080@60
fi
