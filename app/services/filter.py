import json

with open("config.json", "r") as f:
    CONFIG = json.load(f)

def passes_filters(hackathon):

    
    # Collect all active filters
    active_filters = []
    
    # Check online filter
    online_filter = CONFIG.get("online", [])
    if online_filter and True in online_filter:
        active_filters.append("online")
    
    # Check city filter
    city_filter = CONFIG.get("city", [])
    if city_filter and city_filter != [""]:
        active_filters.append("city")
    
    # Check state filter
    state_filter = CONFIG.get("state", [])
    if state_filter and state_filter != [""]:
        active_filters.append("state")
    
    # Check tags filter
    tag_filter = CONFIG.get("tags", [])
    if tag_filter and tag_filter != [""]:
        active_filters.append("tags")
    
    # Check name_contains filter
    name_filter = CONFIG.get("name_contains", [])
    if name_filter and name_filter != [""]:
        active_filters.append("name_contains")
    
    # If no active filters, accept everything
    if not active_filters:
        return True
    
    # Now check if hackathon matches ANY filter
    matches = []
    
    # Check online
    if "online" in active_filters:
        is_online = hackathon.get("online", False)
        if is_online:
            matches.append(True)
            return True  # Early return for efficiency
    
    # Check city
    if "city" in active_filters:
        hack_city = hackathon.get("city", "")
        if any(city.lower() in hack_city.lower() for city in city_filter if city):
            matches.append(True)
            return True
    
    # Check state
    if "state" in active_filters:
        hack_state = hackathon.get("state", "")
        if hack_state in state_filter:
            matches.append(True)
            return True
    
    # Check tags
    if "tags" in active_filters:
        hack_tags = hackathon.get("tags", [])
        if hack_tags:
            if any(tag.lower() in [t.lower() for t in hack_tags] for tag in tag_filter if tag):
                matches.append(True)
                return True
    
    # Check name_contains
    if "name_contains" in active_filters:
        hack_name = hackathon.get("name", "")
        if any(substr.lower() in hack_name.lower() for substr in name_filter if substr):
            matches.append(True)
            return True
    
    # If we got here, no filters matched
    return False