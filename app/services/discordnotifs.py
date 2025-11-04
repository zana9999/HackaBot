import requests

def send_DiscordMessage(hackathons):
    if not hackathons:
        return

    webhook_url = "https://discord.com/api/webhooks/1434024390806339675/mFWAXRmqnirbcJWq2PLBZjBCr6TyiiziCl5eB1QZFS4tSdlkWmfRq3QsYV6u3VpDmrPf"

    CHUNK_SIZE = 10 

    for i in range(0, len(hackathons), CHUNK_SIZE):
        chunk = hackathons[i:i+CHUNK_SIZE]
        embed_fields = []

        for h in chunk:
            parts = h.split(" | ")
            title = parts[0] 
            raw_location = parts[1] if len(parts) > 1 else ""
            location = raw_location.replace(",", "").strip() or "ONLINE"

            dates = parts[2] if len(parts) > 2 else ""
            link = parts[3] if len(parts) > 3 else ""
            description = f"📍 {location}\n🗓️ {dates}\n🔗({link})"
            
            embed_fields.append({
                "name": title,
                "value": description,
                "inline": False
            })


        payload = {
            "embeds": [{
                "title": "🌟 New Hackathons Added! 🌟",
                "color": 0xE4A0B7,
                "fields": embed_fields
            }]
        }

        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204 or response.status_code == 200:
            print("Discord embed sent!")
        else:
            print(f"Failed to send Discord embed: {response.status_code}, {response.text}")


