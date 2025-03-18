function sendToSlack_debug {
    $Uri = "https://hooks.slack.com/services/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"

    New-SlackMessageAttachment -Text "dummy" -Color "#3192DC" -AuthorName "dummyAuthor" -Fallback "failed" |
    New-SlackMessage | Send-SlackMessage -Uri $Uri

}
sendToSlack_debug