"""
Quick test for network PvP module.
Tests protocol serialization and basic message flow.
"""

import json
from protocol import MessageType, MessageBuilder, Messages, GameSettings

def test_protocol():
    """Test protocol message creation and parsing."""
    print("Testing protocol...")
    
    # Test move message
    move_msg = Messages.make_move(3, 4, "black")
    assert move_msg["type"] == "make_move"
    assert move_msg["x"] == 3
    assert move_msg["y"] == 4
    assert move_msg["color"] == "black"
    
    # Test serialization
    serialized = MessageBuilder.serialize(move_msg)
    parsed = MessageBuilder.parse(serialized)
    assert parsed == move_msg
    
    # Test game settings
    settings = GameSettings(board_size=19, rules="chinese", komi=7.5)
    settings_dict = settings.to_dict()
    assert settings_dict["board_size"] == 19
    
    # Test room creation message
    room_msg = Messages.create_room("Test Room", settings)
    assert room_msg["type"] == "create_room"
    assert room_msg["name"] == "Test Room"
    
    print("✅ Protocol tests passed")

def test_message_types():
    """Test all message types are strings."""
    print("Testing message types...")
    
    for mt in MessageType:
        assert isinstance(mt.value, str)
        assert len(mt.value) > 0
    
    print("✅ Message type tests passed")

if __name__ == "__main__":
    test_protocol()
    test_message_types()
    print("✅ All tests passed!")
