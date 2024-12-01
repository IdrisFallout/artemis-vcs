[Setup]
AppName=Artemis VCS
AppVersion=0.1.0
DefaultDirName={autopf}\Artemis
DefaultGroupName=Artemis
LicenseFile=LICENSE
OutputDir=.\output
OutputBaseFilename=artemis_installer
SetupIconFile=assets\artemis.ico

[Files]
Source: "dist\artemis.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: string; ValueName: "Path"; ValueData: "{app}"; Flags: uninsdeletevalue

[Icons]
Name: "{autoprograms}\Artemis"; Filename: "{app}\artemis.exe"
