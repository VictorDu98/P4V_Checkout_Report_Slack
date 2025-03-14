Persistent

SetTimer(RunBatchScript, 60000) ; Time in milliseconds (60000 = 60s)
Return

RunBatchScript(){
	currentTime := FormatTime(, "Time")
	if (currentTime= "8:55 PM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\1.0.4_dual_server\CheckOutP4VServer1.bat")
	}
	if (currentTime= "8:57 PM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\1.0.4_dual_server\CheckOutP4VServer2.bat")
	}
	if (currentTime= "11:50 PM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\1.0.4_dual_server\CheckOutP4VServer1.bat")
	}
    if (currentTime= "11:57 PM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\1.0.4_dual_server\CheckOutP4VServer2.bat")
	}
	if (currentTime= "1:55 AM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\1.0.4_dual_server\CheckOutP4VServer1.bat")
	}
	if (currentTime= "1:57 AM"){
		Run("D:\Powershell_script\I38_P4CheckOutReport\unstable\1.0.4_dual_server\CheckOutP4VServer2.bat")
	}
}
