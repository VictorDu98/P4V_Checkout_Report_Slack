Software requirement:
- Window batch 
- Window Powershell version atleast 5.1.22621.4391
- Autohotkey v2 https://www.autohotkey.com/
- install PSSlack module for Powershell https://www.powershellgallery.com/packages/PSSlack/1.0.6


Info requirement:
- Specify output address for text file (Lookup CheckOutP4V.ps1 variable $OUTPUT)
- A P4V account (with password)
- A Slack channel hook address (Setup with "GameContentNotifyBot" app on slack) e,g: 
    "https://hooks.slack.com/services/xxxxxx/xxxxxxxxx/xxxxxxxxxxxx"
- Json file that contains P4 user info
- An autohotkey script that trigger .bat file at certain time

Future update:
- Convert powershell and bat script into python syntax (WIP in dev 1.0.4)
- Develop UI
- Remove hardcoded P4V password on script, and let user input it manually
- Support cross-projects algorithm
