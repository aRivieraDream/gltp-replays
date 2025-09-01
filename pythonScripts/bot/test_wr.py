#!/usr/bin/env python3
"""Test script to verify world record lookup functionality."""

from utils import get_game_info
from maps import get_maps
from replay_manager import get_wr_entry

def test_world_record_lookup():
    """Test world record lookup for a known map."""
    # Test direct world record lookup
    print("Testing direct world record lookup...")
    wr = get_wr_entry('82514')
    if wr:
        print(f"✅ Found world record for map 82514: {wr['record_time']}ms by {wr['capping_player']}")
    else:
        print("❌ No world record found for map 82514")
    
    # Test through get_game_info
    print("\nTesting get_game_info...")
    maps = get_maps()
    test_map = next((m for m in maps if m['map_id'] == '82514'), None)
    
    if test_map:
        print(f"Found test map: {test_map['name']} with preset: {test_map['preset']}")
        info = get_game_info(test_map['preset'])
        print(f"Game info:\n{info}")
    else:
        print("❌ Test map 82514 not found in maps list")

if __name__ == "__main__":
    test_world_record_lookup()
