import requests
import json

# Replace with your actual webhook URL
webhook_url = 'https://prod-93.southeastasia.logic.azure.com:443/workflows/7aaf012f794f47a4be63ff3e35fa9877/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=8yHEY2BHprJlXKYQKCsI92qXucAa7BkgaLTzX7POYSc'
a = """
mutli line
xuong dong
"""
# Message payload
message = {
    "text": a
}

# Send POST request
response = requests.post(
    webhook_url,
    data=json.dumps(message),
    headers={'Content-Type': 'application/json'}
)

# Check response
if response.status_code == 202:
    print("Message sent successfully!")
else:
    print(f"Failed to send message. Status code: {response.status_code}")
