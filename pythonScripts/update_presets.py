# This script is used to update the map_metadata.json (used with the presets.json) file with the latest
# map difficulty and balls required data from the Google Sheet.
import requests
import json
import io
import csv

"""Splits the categories from spreadsheet into an array based on comma separation.
Example: 'Solo, Checkpoint, Unlimited Jumps, Reversed' = [Solo, Checkpoint, Unlimited Jumps, Reversed]
"""
def split_categories(category_row):
    if not category_row:
        return []
    return [category.strip() for category in category_row.split(',')]

def get_map_metadata():
    # URL for the Google Sheet export
    url = "https://docs.google.com/spreadsheets/d/1OnuTCekHKCD91W39jXBG4uveTCCyMxf9Ofead43MMCU/export"

    # Parameters for the export
    params = {
        "format": "csv",
        "id": "1OnuTCekHKCD91W39jXBG4uveTCCyMxf9Ofead43MMCU",
        "gid": "1775606307"  # This is the gid for the Map Difficulty BackEnd tab
    }

    # Fetch the data
    response = requests.get(url, params=params)
    csv_file = io.StringIO(response.text, newline="")

    # Read the CSV
    reader = csv.DictReader(csv_file)

    # Process the data
    map_metadata = {}
    for row in reader:
        map_name = row["Map / Player"]
        # Clean the map name (remove " by Author" part)
        map_name = map_name.rsplit(" by ", 1)[0] if " by " in map_name else map_name

        map_metadata[map_name] = {
            "difficulty": row["Final Rating"],
            "balls_req": row["Min\nBalls \nRec"],
            "preset": row["Group Preset"],
            "categories": split_categories(row["Category"]),
            "grav_or_classic": row["Grav or\nClassic"]
        }

    # Save to a JSON file
    with open("map_metadata.json", "w") as f:
        json.dump(map_metadata, f, indent=4)

    print(f"Saved metadata for {len(map_metadata)} maps to map_metadata.json")



if __name__ == "__main__":
    """
    This script is used to update the map_metadata.json file with the latest
    map difficulty and balls required data from the Google Sheet.
    """
    get_map_metadata()
