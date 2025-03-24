Persistent

SetTimer(RunBatchScript, 60000) ; Time in milliseconds (60000 = 60s)
Return

RunBatchScript(){
	currentTime := FormatTime(, "Time")
	if (currentTime= "6:16 PM"){
		RunWait("D:\Powershell_script\I38_P4CheckOutReport\CheckOutP4VServer1.bat")
		Run("D:\Powershell_script\I38_P4CheckOutReport\CheckOutP4VServer2.bat")
	}
	if (currentTime= "11:50 PM"){
		RunWait("D:\Powershell_script\I38_P4CheckOutReport\CheckOutP4VServer1.bat")
		Run("D:\Powershell_script\I38_P4CheckOutReport\CheckOutP4VServer2.bat")
	}
	if (currentTime= "1:55 AM"){
		RunWait("D:\Powershell_script\I38_P4CheckOutReport\CheckOutP4VServer1.bat")
		Run("D:\Powershell_script\I38_P4CheckOutReport\CheckOutP4VServer2.bat")
	}
}
