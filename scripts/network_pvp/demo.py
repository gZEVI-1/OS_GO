"""
OS-GO Network PvP Demo
========================

Quick start script for local testing of network PvP.
Runs server and two clients in separate processes for demonstration.

Usage:
    python demo.py

This will:
1. Start the WebSocket server
2. Launch Client 1 (Alice) - creates a room
3. Launch Client 2 (Bob) - joins the room
4. Simulate a short game

Requirements:
    - All dependencies installed
    - Terminal with support for multiple processes
"""

import asyncio
import subprocess
import sys
import time
import signal
import os


def start_server():
    """Start the WebSocket server in background."""
    print("🚀 Starting server...")
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", 
         "--host", "localhost", "--port", "8765"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(2)  # Wait for server to start
    return process


def start_client(name, delay=0):
    """Start a client with given name."""
    if delay:
        time.sleep(delay)
    print(f"👤 Starting client: {name}")
    process = subprocess.Popen(
        [sys.executable, "client.py", "ws://localhost:8765/ws", "-u", name],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process


def main():
    """Run demo."""
    print("="*60)
    print("  OS-GO Network PvP Demo")
    print("="*60)
    
    server = None
    clients = []
    
    try:
        # Start server
        server = start_server()
        
        # Start clients
        client1 = start_client("Alice")
        clients.append(client1)
        
        client2 = start_client("Bob", delay=3)
        clients.append(client2)
        
        print("✅ Demo running!")
        print("   Server: ws://localhost:8765")
        print("   Client 1: Alice")
        print("   Client 2: Bob")
        print("Press Ctrl+C to stop...")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("🛑 Stopping demo...")
    finally:
        # Cleanup
        for client in clients:
            client.terminate()
        if server:
            server.terminate()
        print("✅ Demo stopped")


if __name__ == "__main__":
    main()
