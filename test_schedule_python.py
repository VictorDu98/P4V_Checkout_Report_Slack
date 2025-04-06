import time
import os
import subprocess
# Thời gian chạy (11:53 sáng)
target_time = "15:06"


def main():
    # Vòng lặp kiểm tra thời gian hiện tại
    while True:
        current_time = time.strftime("%H:%M")  # Lấy thời gian định dạng HH:MM
        if current_time == target_time:
            subprocess.run(["powershell", "-File", r"D:\tools\P4V_Checkout_Report_Slack\debug.ps1"], capture_output=True, text=True)
        time.sleep(60)  # Kiểm tra lại sau 30 giây

#main()
result = subprocess.run(r"/test_schedule_python.py")
print(result.stdout)