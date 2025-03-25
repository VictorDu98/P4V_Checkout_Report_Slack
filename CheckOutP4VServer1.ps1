#Author : toan.du
Clear-Host

## Script flow ##

#0. Login P4 

#1. Read userInfo.json each key "AccountName"

#2. Delete current existing check_out_log
    #2.1 Loop each key "AccountName" to query opened P4V files by using P4 commandline
        #2.2 Append to text file named check_out_log.txt

#3. Read check_out_log content, filter line-by-line string by regex expression
    #3.1 Ignore "mark for add" P4V opened files
    #3.2 Return workspace name as results (Non-duplicated)

#4. Delete current existing checkOutReport_[DEPARTMENT].txt
    #4.1 Compare each items from results with each valuue from userInfo.json key "WorkSpace" to find a match
    #4.2 If match , then appends to text file checkOutReport_[DEPARTMENT].txt

#5. Read contents of checkOutReport_[DEPARTMENT].txt
    #5.1 If exist, send contents to Slack channel

function OutputP4Log {
    $verify_exist = Test-Path -Path $OUTPUT_LOG
    if ($verify_exist)
    {
        Remove-Item $OUTPUT_LOG
    }

    $accounts_name = $JSON.info.AccountName
    foreach ($name in $accounts_name)
    {
        $i = 0
        $verify = p4 opened -u $name
        if ($verify)
        {
            "-------------------------$name----------------------------" | Out-File -FilePath $OUTPUT_LOG -Append -Encoding UTF8
            p4 opened -u $name | Select-String -Pattern "edit" -SimpleMatch | Out-File -FilePath $OUTPUT_LOG -Append -Encoding UTF8
            " "| Out-File -FilePath $OUTPUT_LOG -Append -Encoding UTF8
        }
        $i += 1
    }
}
function FilterLogFile {
    <#
    .SYNOPSIS
        Read each lines of textfile then use regex expression to get workspace name that leave file checked out on P4
    .DESCRIPTION
        Log file output string that always come with user@workspace in each lines
        Use regex expression to filter "mark for add" files and files that have status of checked-out files
        Lines of text that matched regex will be returned in a non-duplicated array
        Lines of text that fit in ignore case will be ignored since the file itself it's not on depot yet
    #>
    $result = [System.Collections.Generic.HashSet[string]]::new()
    $regex= "by\s+(.*?)(\s+\*exclusive\*)?(\s+\*locked\*)?$"

    $verify_empty = Get-Content -Path $OUTPUT_LOG
    if($null -eq $verify_empty){
        return $null
    }

    foreach($line in Get-Content -Path $OUTPUT_LOG)
    {
        $match= $line -match $regex
        #Write-Host $match
        if($match){
            if($matches[1] -eq $null){
                continue
            }
            $string = $matches[1]
            #Split string with delimiter "@" and take workspace name by index 1
            $workspace_name = $string -split "@"
            $result.Add($workspace_name[1]) | Out-Null
            }
        }
    return $result
}
function findUser{
    $result = FilterLogFile
    $json_workspaces = $JSON.info.WorkSpace
    $json_index= @()

    if(Test-Path -Path $OUTPUT_REPORT_ENV){
        Write-Host $OUTPUT_REPORT_ENV
        Remove-Item $OUTPUT_REPORT_ENV
    }
    if(Test-Path -Path $OUTPUT_REPORT_VFX){
        Write-Host $OUTPUT_REPORT_VFX
        Remove-Item $OUTPUT_REPORT_VFX
    }
    if($null -eq $result){
        return $null
    }
    foreach($found_workspace in $result){
        #Write-Host $found_workspace
        $i=0
        foreach($json_workspace in $json_workspaces){
            $match = $found_workspace -match $json_workspace
            if($match -and $json_index -notcontains $i){
                $json_index+=$i
            }
            $i+=1
        }
    }

    foreach($index in $json_index){
        if($JSON.info.Department[$index] -eq "VFX"){
            $report = $JSON.info.Project[$index] + " - " + $JSON.info.UserName[$index] + " - " + $JSON.info.WorkSpace[$index] + " - " + $JSON.info.Email[$index]
            $report | Out-File -FilePath $OUTPUT_REPORT_VFX -Append -Encoding UTF8
            $i+=1
        }
    }
    foreach($index in $json_index){
        if($JSON.info.Department[$index] -eq "ENV"){
            $report = $JSON.info.Project[$index] + " - " + $JSON.info.UserName[$index] + " - " + $JSON.info.WorkSpace[$index] + " - " + $JSON.info.Email[$index]
            $report | Out-File -FilePath $OUTPUT_REPORT_ENV -Append -Encoding UTF8
        }
    }

    #foreach($index in $json_index){
        #if($JSON.info.Department[$index] -eq "[DEPARTMENT]"){
            #$report = $JSON.info.Project[$index] + " - " + $JSON.info.UserName[$index] + " - " + $JSON.info.WorkSpace[$index] + " - " + $JSON.info.Email[$index]
            #$report | Out-File -FilePath $OUTPUT_REPORT_[DEPARTMENT] -Append -Encoding UTF8
        #}
    #}
}
function sendToSlack {
    $verify_exist_vfx = Test-Path -Path $OUTPUT_REPORT_VFX
    $verify_exist_env = Test-Path -Path $OUTPUT_REPORT_ENV

    if($verify_exist_vfx){
        Write-Host "Found $OUTPUT_REPORT_VFX"
        $report_txt_vfx = Get-Content -Path $OUTPUT_REPORT_VFX -Raw | Out-String
        New-SlackMessageAttachment -Text "$report_txt_vfx CC: $vfx_producer_slack_user_id"  -Color "#3192DC" -AuthorName "VFX" -Fallback "Hello $vfx_producer_slack_user_id, please help notify these artists about their P4V checked out files." |
        New-SlackMessage | Send-SlackMessage -Uri $Uri
        return
    }
    if($verify_exist_env){
        Write-Host "Found $OUTPUT_REPORT_ENV"
        $report_txt_env = Get-Content -Path $OUTPUT_REPORT_ENV -Raw | Out-String
        New-SlackMessageAttachment -Text "$report_txt_env CC: $env_producer_slack_user_id" -Color "#2F783B" -AuthorName "ENV" -Fallback "Hello $env_producer_slack_user_id, please help notify these artists about their P4V checked out files." |
        New-SlackMessage | Send-SlackMessage -Uri $Uri
        return
    }
    Write-Host "No one checked out files to report"
}
function main {
    p4 set P4CONFIG=$P4CONFIG
    $password | p4 login
    ####
    OutputP4Log
    findUser -output $OUTPUT
    sendToSlack
    ####
}



$currentDate = Get-Date
$formattedDate = $currentDate.ToString("yyMMdd")

# Server Path
$OUTPUT = "\\virtuosgames.com\spxprojects\I38\11_Technical\P4V\P4CheckOutReport"
$OUTPUT_LOG = $OUTPUT + "\check_out_log_server_01_$formattedDate.txt"
$OUTPUT_REPORT_ENV = $OUTPUT + "\check_out_report_server_01_ENV_$formattedDate.txt"
$OUTPUT_REPORT_VFX = $OUTPUT + "\check_out_report_server_01_VFX_$formattedDate.txt"
$JSON = Get-Content -Path $PSScriptRoot\userinfo.json -Raw | Out-String | ConvertFrom-Json

# P4 account credential
$P4CONFIG = $PSScriptRoot + "\p4config_server01.txt"
$password = "r|1S+'x/rK0u"

# Slack channel webhook address to send message *IMPORTANT*
#$Uri = "https://hooks.slack.com/services/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"
$Uri = "https://hooks.slack.com/services/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"
$vfx_producer_slack_user_id = "<@U07PN0VLVCJ>"
$env_producer_slack_user_id = "<@U06TZTW93LZ>"

main