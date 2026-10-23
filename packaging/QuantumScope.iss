#define MyAppName "QuantumScope"
#ifndef MyAppVersion
#define MyAppVersion "0.4.1"
#endif
#define MyAppPublisher "QuantumScope contributors"
#define MyAppURL "https://github.com/Onimee58/QuantumScope"
[Setup]
AppId={{A39EA855-AE51-4C93-A7E3-005ADBDF43AB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
DefaultDirName={autopf}\QuantumScope
DefaultGroupName=QuantumScope
UninstallDisplayIcon={app}\QuantumScope.exe
OutputDir=..\dist\installers
OutputBaseFilename=QuantumScope-{#MyAppVersion}-Setup
SetupIconFile=..\src\quantumscope\assets\quantumscope.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
DisableProgramGroupPage=yes
[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked
[Files]
Source: "..\dist\QuantumScope\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{autoprograms}\QuantumScope"; Filename: "{app}\QuantumScope.exe"; IconFilename: "{app}\QuantumScope.exe"
Name: "{autodesktop}\QuantumScope"; Filename: "{app}\QuantumScope.exe"; Tasks: desktopicon
[Run]
Filename: "{app}\QuantumScope.exe"; Description: "Launch QuantumScope"; Flags: nowait postinstall skipifsilent
