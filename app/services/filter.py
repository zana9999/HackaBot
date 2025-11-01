import json

with open("config.json", "r") as f:
    CONFIG = json.load(f)

import json

with open("config.json", "r") as f:
    CONFIG = json.load(f)

def passes_filters(hackathon):
    for key, values in CONFIG.items():
        if not values or values == [""]:
            continue  # skip empty filter

        hack_val = hackathon.get(key)
        if hack_val is None:
            return False

        if key == "tags":
            if not any(t.lower() in [v.lower() for v in values] for t in hack_val):
                return False
        elif key == "name_contains":
            if not any(substr.lower() in hack_val.lower() for substr in values):
                return False
        elif key == "city":
            if hack_val == "" and True in CONFIG.get("online", []):
                continue  # allow online events with empty city
            if not any(v.lower() in hack_val.lower() for v in values):
                return False
        else:
            if hack_val not in values:
                return False

    return True
