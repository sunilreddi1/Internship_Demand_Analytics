Set WshShell = CreateObject("WScript.Shell")
strDesktop = WshShell.SpecialFolders("Desktop")
Set oMyShortcut = WshShell.CreateShortcut(strDesktop & "\Internship Analytics.lnk")

oMyShortcut.TargetPath = "cmd.exe"
oMyShortcut.Arguments = "/k cd /d ""C:\Users\sunil\Desktop\Internship_Demand_Analytics"" && public_url.bat"
oMyShortcut.WorkingDirectory = "C:\Users\sunil\Desktop\Internship_Demand_Analytics"
oMyShortcut.Description = "One-click public access to Internship Analytics app"
oMyShortcut.IconLocation = "C:\Windows\System32\SHELL32.dll,13"
oMyShortcut.Save

WScript.Echo "✅ Desktop shortcut created! Double-click 'Internship Analytics' on your desktop to get your public URL."