Info requirement:
- A valid P4 credential
- Microsoft Workflows job that post message into Group chat , with channel webhook provided, e.g:
 "https://default2ca815949a7142a0a4870fc9de27d8.34.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/xxxxxxxxxxxx"
- Deprecated: A Slack channel hook address (Setup with "GameContentNotifyBot" app on slack) e,g: 
 "https://hooks.slack.com/services/xxxxxx/xxxxxxxxx/xxxxxxxxxxxx"
-  Tool preset that has been setup based on root>presets>_template

![img_10.png](img_10.png)
![img_11.png](img_11.png)


Future update, striked through mean done:
- ~~Convert powershell and bat script into python syntax~~
- Develop UI
- ~~Remove hardcoded P4V password on script, and let user input it manually~~
- ~~Support mutiple-projects~~
- Support both Slack and Workflows message posting
- Generate .p4trust for first time preset login
- Have a test case system for basic validation
---
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
-----
What is a preset?

A preset can be known as an entity that tool will recognize as task, where task's will queue up and run as waterfall orderly.
For current state, we does not have an system that manage task's, but as core we can setup mutiple task's and delegate the tool to run them daily.


A preset consist following files:
```
root
  - presets
       - Preset name
            .p4config
            .p4tickets(Generated via p4 login)
            .p4trust ( N/A for now )
            config.json
```


----
Slack chatbot setup:
1. A Slack account within Virtuos Vietnam ( For SPX studio)
2. Create a new channel with blank template

 ![img_1.png](img_1.png) ![img_2.png](img_2.png) ![img_3.png](img_3.png) ![img_4.png](img_4.png) ![img_5.png](img_5.png)
3. Add app into channel
https://slack.com/oauth/v2/authorize?client_id=697626830967.8011987954565&scope=incoming-webhook&user_scope=
 ![img.png](img.png)
 
   *If you can’t find any channel it doesn’t mean the channel not existed , studio DG agent has blocked the outgoing rules in behind the scene , so as SPX TA you can setup Slack chatbot via vngate for fast workaround*


4. Login website “https://api.slack.com/apps/A080BV1U2GM” and “Add new WebHook to Workspace”
![img_6.png](img_6.png)
   If you cannot access this App with no authorization , please contact toan.du  to add you as Collaborators, or you can setup the chatbot app yourself.
![img_7.png](img_7.png)
---
