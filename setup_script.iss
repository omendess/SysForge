[Setup]
AppName=SysForge
SetupIconFile=icon.ico
AppVersion=5.0.0.1
AppPublisher=Orlando Mendes
AppCopyright=Copyright (C) 2026 Orlando Mendes
VersionInfoCompany=Orlando Mendes
VersionInfoDescription=SysForge Host - Motor de Implantação e Manutenção
VersionInfoVersion=5.0.0.1
DefaultDirName={autopf}\SysForge
DefaultGroupName=SysForge
OutputDir=Output
OutputBaseFilename=SysForge_Setup_v5
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\SysForge_Host.exe"; DestDir: "{app}"; Flags: ignoreversion
; Pode incluir outros arquivos do projeto se necessário

[Icons]
Name: "{group}\SysForge"; Filename: "{app}\SysForge_Host.exe"
Name: "{commondesktop}\SysForge"; Filename: "{app}\SysForge_Host.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SysForge_Host.exe"; Description: "{cm:LaunchProgram,SysForge}"; Flags: nowait postinstall skipifsilent shellexec
