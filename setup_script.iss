#define MyAppVersion "1.0.3"

[Setup]
AppName=SysForge
SetupIconFile=icon.ico
AppVersion={#MyAppVersion}
AppPublisher=Singularity Dot
AppCopyright=Copyright (C) 2026 Singularity Dot
VersionInfoCompany=Singularity Dot
VersionInfoDescription=SysForge Host - Motor de Implantação e Manutenção
VersionInfoVersion={#MyAppVersion}.0
DefaultDirName={autopf}\SysForge
DefaultGroupName=SysForge
OutputDir=Output
OutputBaseFilename=SysForge_Setup_v{#MyAppVersion}
WizardStyle=modern
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\SysForge_Host_v{#MyAppVersion}.exe"; DestDir: "{app}"; Flags: ignoreversion
; Pode incluir outros arquivos do projeto se necessário

[Icons]
Name: "{group}\SysForge"; Filename: "{app}\SysForge_Host_v{#MyAppVersion}.exe"
Name: "{commondesktop}\SysForge"; Filename: "{app}\SysForge_Host_v{#MyAppVersion}.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\SysForge_Host_v{#MyAppVersion}.exe"; Description: "{cm:LaunchProgram,SysForge}"; Flags: nowait postinstall skipifsilent shellexec
