"""
OS-GO Network Configuration
=============================

Centralized configuration for network PvP module.
Supports environment variables and .env files.

Usage:
    from config import ServerConfig, ClientConfig
    
    server_cfg = ServerConfig.from_env()
    client_cfg = ClientConfig.from_env()
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "0.0.0.0"
    port: int = 8765
    max_rooms: int = 100
    max_room_age_minutes: int = 60
    jwt_secret: str = "change-me-in-production"
    log_level: str = "info"
    enable_cors: bool = True
    
    @classmethod
    def from_env(cls) -> "ServerConfig":
        """Load configuration from environment variables."""
        return cls(
            host=os.getenv("WS_HOST", "0.0.0.0"),
            port=int(os.getenv("WS_PORT", "8765")),
            max_rooms=int(os.getenv("MAX_ROOMS", "100")),
            max_room_age_minutes=int(os.getenv("MAX_ROOM_AGE", "60")),
            jwt_secret=os.getenv("JWT_SECRET", "change-me-in-production"),
            log_level=os.getenv("LOG_LEVEL", "info"),
            enable_cors=os.getenv("ENABLE_CORS", "true").lower() == "true",
        )


@dataclass
class ClientConfig:
    """Client configuration."""
    server_url: str = "ws://localhost:8765/ws"
    username: str = ""
    auto_reconnect: bool = True
    reconnect_delay: int = 5
    max_reconnect_attempts: int = 3
    enable_sounds: bool = False
    save_games_dir: str = "./games/pvp/"
    
    @classmethod
    def from_env(cls) -> "ClientConfig":
        """Load configuration from environment variables."""
        return cls(
            server_url=os.getenv("WS_SERVER_URL", "ws://localhost:8765/ws"),
            username=os.getenv("WS_USERNAME", ""),
            auto_reconnect=os.getenv("WS_AUTO_RECONNECT", "true").lower() == "true",
            reconnect_delay=int(os.getenv("WS_RECONNECT_DELAY", "5")),
            max_reconnect_attempts=int(os.getenv("WS_MAX_RECONNECT", "3")),
            save_games_dir=os.getenv("WS_SAVE_DIR", "./games/pvp/"),
        )
