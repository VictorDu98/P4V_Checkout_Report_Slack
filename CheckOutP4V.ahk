Persistent

SetTimer(RunBatchScript, 60000) ; Time in milliseconds (60000 = 60s)
Return

RunBatchScript(){
	currentTime := FormatTime(, "Time")
	if (currentTime= "8:55 PM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\CheckOutP4VServer1.bat")
	}
	if (currentTime= "9:00 PM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\CheckOutP4VServer2.bat")
	}
	if (currentTime= "11:50 PM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\CheckOutP4VServer1.bat")
	}
    if (currentTime= "12:59 PM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\CheckOutP4VServer2.bat")
	}
	if (currentTime= "1:50 AM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\CheckOutP4VServer1.bat")
	}
	if (currentTime= "1:59 AM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\CheckOutP4VServer2.bat")
	}
}
