# 在红米本的 Windows 里右键 "使用 PowerShell 运行"，结果写到同目录 hwinfo.txt
$out = Join-Path $PSScriptRoot "hwinfo.txt"
& {
  "=== 型号 / BIOS ==="
  Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model, SystemFamily | Format-List
  Get-CimInstance Win32_BIOS | Select-Object SMBIOSBIOSVersion, ReleaseDate | Format-List
  Get-CimInstance Win32_Processor | Select-Object Name | Format-List
  "=== 硬盘 ==="
  Get-PhysicalDisk | Select-Object FriendlyName, BusType, MediaType, Size | Format-Table -AutoSize
  "=== 显卡 / 声卡 / 网卡 / 触摸板 / 蓝牙 / USB 控制器 (PnP ID) ==="
  Get-PnpDevice -PresentOnly | Where-Object {
    $_.Class -in @('Display','MEDIA','AudioEndpoint','Net','HIDClass','Mouse','Keyboard','Bluetooth','USB','System') -and
    $_.InstanceId -match '^(PCI|HDAUDIO|ACPI|HID|INTELAUDIO|USB\\VID_8087)'
  } | Sort-Object Class | Select-Object Class, FriendlyName, InstanceId | Format-Table -AutoSize -Wrap
} *>&1 | Out-File -Encoding utf8 $out -Width 300
Write-Host "已保存到 $out"
