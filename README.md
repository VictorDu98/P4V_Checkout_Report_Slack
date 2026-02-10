## About the Project
<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="doc/img/logo.png" alt="Logo" width="250" height="250">
  </a>

  <h3 align="center">Project-p4-overwatch</h3>

  <p align="center">
    A solution to remind your team to check-in their work!
    <br />
    <a href="https://github.com/othneildrew/Best-README-Template/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/othneildrew/Best-README-Template/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>


<!-- ROADMAP -->
## Roadmap


- [x] Convert powershell and bat script into python syntax
- [x] Support multiple-projects with preset system
    - [ ] Support mutli-thread to run job(s) simultaneously

- [x] Remove hardcoded P4V password, enabled .p4tickets on preset.
  - [ ] Generate .p4trust for preset
- [ ] Develop Frontend and DB and move on from CLI.
- [ ] Provide config.json able to adjust trigger time and iterations
- [ ] Have a test case system for basic validation
- [ ] Support both Slack and Workflows message posting

See the open issues for a full list of proposed features (and known issues).

<!-- WHAT IS A PRESET -->
## What is a preset?


A preset can be known as an entity that tool will recognize as task, where task's will queue up and run as waterfall orderly.

For current state, we does not have an system that manage task's, but as core we can setup mutiple task's and delegate the tool to run them daily via **root>_start.py_**


A preset consist following files:
```
root
  - presets
       - [Preset name]
            .p4config
            .p4tickets(Generated via p4 login)
            .p4trust ( N/A for now )
            config.json
```
You can also view [_template](src/presets/presets/_template) preset for reference:
[.p4config](src/presets/presets/_template/.p4config) , [config.json](src/presets/presets/_template/config.json)

<!-- PREREQUISITES -->
##  Prerequisites
- A valid and working P4 credential
- Microsoft Workflows job that post message into Group chat, with channel webhook provided
  - See tutorial of how to <a href="#workflow-setup">Workflow setup</a></li>
- A valid tool preset that has been setup based on [_template](src/presets/presets/_template)
    
  - See tutorial of how to  <a href="#preset-setup">Preset setup</a></li>

<!-- INSTALLATION -->
## Installation:

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


## Example:


<a id="preset-setup"></a>
## Preset setup
<details>

![19.png](doc/img/19.png)
![20.png](doc/img/20.png)
![21.png](doc/img/21.png)

</details>

<a id="workflow-setup"></a>
## (External)  Workflow setup


<details>

![10.png](doc/img/10.png)
![9.png](doc/img/9.png)
![12.png](doc/img/12.png)
![13.png](doc/img/13.png)
![14.png](doc/img/14.png)
![15.png](doc/img/15.png)
![16.png](doc/img/16.png)
![17.png](doc/img/17.png)
![18.png](doc/img/18.png)

![11.png](doc/img/11.png)

</details>

## (External-Deprecreted) Slack chatbot setup:


<details>
1. A Slack account within Virtuos Vietnam ( For SPX studio)

![1.png](doc/img/1.png)

2. Create a new channel with blank template


![2.png](doc/img/2.png)
![3.png](doc/img/3.png)
![4.png](doc/img/4.png)
![5.png](doc/img/5.png)
3. Add app into channel
https://slack.com/oauth/v2/authorize?client_id=697626830967.8011987954565&scope=incoming-webhook&user_scope=
![6.png](doc/img/6.png)
 
   *If you can’t find any channel it doesn’t mean the channels are not existed , studio DG agent has blocked the outgoing rules in behind the scene , so as SPX TA you can setup Slack chatbot via vngate for fast workaround*


4. Login website “https://api.slack.com/apps/A080BV1U2GM” and “Add new WebHook to Workspace”
![7.png](doc/img/7.png)
   If you cannot access this App with no authorization , please contact toan.du  to add you as Collaborators, or you can setup the chatbot app yourself in case of you needs full control over slack app.
![8.png](doc/img/8.png)
</details>