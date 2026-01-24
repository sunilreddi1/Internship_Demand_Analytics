Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oMyShortcut = WshShell.CreateShortcut(strDesktop & "\Internship Analytics.lnk")
oMyShortcut.TargetPath = "C:\Users\sunil\Desktop\Internship_Demand_Analytics\run_app.bat"
oMyShortcut.WorkingDirectory = "C:\Users\sunil\Desktop\Internship_Demand_Analytics"
oMyShortcut.Description = "Launch Internship Demand Analytics App"
oMyShortcut.Save