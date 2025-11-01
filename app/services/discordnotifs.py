import requests

def send_discord_notification(webhookURL, message):
    data = {
        "content": message
    }
    response = requests.post(webhookURL, json=data)
    if response.status_code == 204:
        print("Discord notification sent!")
    else:
        print(f"Failed to send Discord message: {response.status_code}")