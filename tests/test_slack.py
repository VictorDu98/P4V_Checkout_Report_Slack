def slack_debug(webhook):
    # Define the webhook URL provided by Slack
    webhook_url = webhook

    # Define the message payload
    payload = {
        "text": "Here is a message with an attachment.",
        "attachments": [
            {
                "color": "#3192DC",  # Set the color of the attachment
                "author_name": "Attachment Author",
                "title": "Attachment Title",
                "text": "This is the content of the attachment.",
                "footer": "Attachment Footer",
                "ts": 1234567890  # Timestamp (optional)
            }
        ]
    }

    # Send the POST request to Slack's webhook URL
    response = requests.post(webhook_url, json=payload)

    # Check the response
    if response.status_code == 200:
        print("Message sent successfully.")
        return True
    else:
        print(f"Failed to send message: {response.status_code}, {response.text}")
        return False
