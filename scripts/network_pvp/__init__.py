"""
OS-GO Network PvP Package

Provides client-server infrastructure for online Go matches.
"""

from .protocol import (
    MessageType,
    MessageBuilder,
    Messages,
    GameSettings,
    PlayerInfo,
    RoomInfo,
)

from .client import NetworkClient, ClientConfig, ClientState
from .console_pvp_network import NetworkPvPGame, NetworkGameCallbacks, NetworkGamePhase

__all__ = [
    'MessageType',
    'MessageBuilder',
    'Messages',
    'GameSettings',
    'PlayerInfo',
    'RoomInfo',
    'NetworkClient',
    'ClientConfig',
    'ClientState',
    'NetworkPvPGame',
    'NetworkGameCallbacks',
    'NetworkGamePhase',
]
