$RawDate = (& "C:\Program Files\Git\bin\git.exe" -C "d:\CascadeProjects" log -1 "--format=%aI" 2>$null | Out-String).Trim()
if ($RawDate -match "^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})") {
    $LastCommitTime = "$($Matches[1])$($Matches[2])$($Matches[3])_$($Matches[4])$($Matches[5])"
} else {
    $LastCommitTime = (Get-Date -Format "yyyyMMdd_HHmm")
}
$ShortcutName = "goldkey_ay_maset.Lab_$LastCommitTime"
$Desktop = [Environment]::GetFolderPath("Desktop")
$WindsurfExe = "C:\Users\insus\AppData\Local\Programs\Windsurf\Windsurf.exe"
Get-ChildItem $Desktop -Filter "goldkey_ay_maset.Lab*.lnk" | Remove-Item -Force
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("$Desktop\$ShortcutName.lnk")
$Shortcut.TargetPath = $WindsurfExe
$Shortcut.Arguments = "`"d:\CascadeProjects`""
$Shortcut.WorkingDirectory = "d:\CascadeProjects"
$Shortcut.IconLocation = $WindsurfExe
$Shortcut.Description = "GoldKey InsuSite Lab - Last: $LastCommitTime"
$Shortcut.Save()
Write-Host "OK: $ShortcutName.lnk"
