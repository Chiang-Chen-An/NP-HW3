#!/bin/bash

# Quick start script - starts all required servers
# Run this before testing clients

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Starting Game Store System Servers   ${NC}"
echo -e "${CYAN}========================================${NC}\n"

# Kill any existing servers
echo -e "${YELLOW}Stopping existing servers...${NC}"
pkill -f "python.*database_server" 2>/dev/null
pkill -f "python.*developer_server" 2>/dev/null
pkill -f "python.*lobby_server" 2>/dev/null
sleep 1

# Check database initialization
if [ ! -f "server/database_server/data/users.json" ]; then
    echo -e "${YELLOW}Initializing database...${NC}"
    make init
fi

# Start servers in background with logging
echo -e "${GREEN}Starting Database Server (port 8080)...${NC}"
nohup python3 -m server.database_server.main > logs/database_server.log 2>&1 &
DB_PID=$!
sleep 2

# Check if database server started
if ps -p $DB_PID > /dev/null; then
    echo -e "${GREEN}✓ Database Server started (PID: $DB_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start Database Server${NC}"
    exit 1
fi

echo -e "${GREEN}Starting Developer Server (port 8081)...${NC}"
nohup python3 -m server.developer_server.main > logs/developer_server.log 2>&1 &
DEV_PID=$!
sleep 2

# Check if developer server started
if ps -p $DEV_PID > /dev/null; then
    echo -e "${GREEN}✓ Developer Server started (PID: $DEV_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start Developer Server${NC}"
    exit 1
fi

echo -e "${GREEN}Starting Lobby Server (port 12346)...${NC}"
nohup python3 -m server.lobby_server.main > logs/lobby_server.log 2>&1 &
LOBBY_PID=$!
sleep 2

# Check if lobby server started
if ps -p $LOBBY_PID > /dev/null; then
    echo -e "${GREEN}✓ Lobby Server started (PID: $LOBBY_PID)${NC}"
else
    echo -e "${RED}✗ Failed to start Lobby Server${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All Servers Started Successfully!    ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}Server Status:${NC}"
echo -e "  Database Server: ${GREEN}Running${NC} (PID: $DB_PID, Port: 8080)"
echo -e "  Developer Server: ${GREEN}Running${NC} (PID: $DEV_PID, Port: 8081)"
echo -e "  Lobby Server: ${GREEN}Running${NC} (PID: $LOBBY_PID, Port: 12346)"
echo ""
echo -e "${CYAN}Logs:${NC}"
echo -e "  Database: logs/database_server.log"
echo -e "  Developer: logs/developer_server.log"
echo -e "  Lobby: logs/lobby_server.log"
echo ""
echo -e "${CYAN}To start clients:${NC}"
echo -e "  Developer Client: ${YELLOW}make developer_client${NC}"
echo -e "  Lobby Client: ${YELLOW}make lobby_client${NC}"
echo ""
echo -e "${CYAN}To stop all servers:${NC}"
echo -e "  ${YELLOW}./stop_servers.sh${NC} or ${YELLOW}make clean${NC}"
echo ""

# Save PIDs to file for easy cleanup
echo "$DB_PID" > .server_pids
echo "$DEV_PID" >> .server_pids
echo "$LOBBY_PID" >> .server_pids
