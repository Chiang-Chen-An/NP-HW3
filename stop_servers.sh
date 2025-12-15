#!/bin/bash

# Stop all servers script

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping all servers...${NC}"

# Kill by process name
pkill -f "python.*database_server" 2>/dev/null
pkill -f "python.*developer_server" 2>/dev/null
pkill -f "python.*lobby_server" 2>/dev/null

# Also kill by PID if file exists
if [ -f ".server_pids" ]; then
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            kill $pid 2>/dev/null
        fi
    done < .server_pids
    rm .server_pids
fi

sleep 1

echo -e "${GREEN}All servers stopped.${NC}"

# Show remaining Python processes (for verification)
if ps aux | grep -E "python.*server" | grep -v grep > /dev/null; then
    echo -e "${RED}Warning: Some server processes may still be running:${NC}"
    ps aux | grep -E "python.*server" | grep -v grep
else
    echo -e "${GREEN}✓ No server processes found.${NC}"
fi
