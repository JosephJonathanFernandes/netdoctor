; NetDoctor Inno Setup Installer Script
; To compile: iscc installer/netdoctor.iss
; Requires: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)

#define MyAppName "NetDoctor"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Joseph Jonathan Fernandes"
#define MyAppURL "https://github.com/JosephJonathanFernandes/netdoctor"
#define MyAppExeName "NetDoctor.exe"

[Setup]
AppId={{{E3F2A1B4-C5D6-7890-ABCD-EF1234567890}}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\NetDoctor
DefaultGroupName=NetDoctor
AllowNoIcons=yes
LicenseFile=LICENSE
OutputDir=installer/output
OutputBaseFilename=NetDoctor-Setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\NetDoctor.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "translations\*"; DestDir: "{app}\translations"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: dirifempty; Dir: "{app}\translations"
Type: dirifempty; Dir: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
