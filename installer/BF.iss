#define MyAppName "BF"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "BF Assistant"
#define MyAppExeName "BF.exe"

[Setup]
AppId={{60B84B9D-73C6-4502-8D6F-5DE0560535A2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\BF
DefaultGroupName=BF
DisableProgramGroupPage=yes
OutputDir=..\release
OutputBaseFilename=BF-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\bf.ico

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le bureau"; GroupDescription: "Raccourcis"; Flags: checkedonce
Name: "startup"; Description: "Demarrer BF automatiquement avec Windows"; GroupDescription: "Demarrage"; Flags: unchecked

[Files]
Source: "..\dist\BF\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\BF"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\BF"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\BF"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Lancer BF"; Flags: nowait postinstall skipifsilent
