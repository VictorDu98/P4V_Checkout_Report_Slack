Info requirement:
- Specify output address for text file (Lookup CheckOutP4V.ps1 variable $OUTPUT)
- A P4V account (with password)
- A Slack channel hook address (Setup with "GameContentNotifyBot" app on slack) e,g: 
    "https://hooks.slack.com/services/xxxxxx/xxxxxxxxx/xxxxxxxxxxxx"
- Json file that contains P4 user info
- An autohotkey script that trigger .bat file at certain time

Future update:
- Convert powershell and bat script into python syntax
- Develop UI
- Remove hardcoded P4V password on script, and let user input it manually
- Support cross-projects algorithm


Installation:
1. First, cd terminal into your root directory

2. Make new virtual env
```
python -m venv venv 
```

3. Activate venv
```
venv\Scripts\activate
```

4. Install dependencies

```
pip install -r requirements.txt  
```