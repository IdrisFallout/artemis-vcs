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
; Append the application directory to the user's PATH environment variable and refresh the PATH.
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Flags: uninsdeletevalue

[Run]
; Refresh the environment variables to avoid requiring a system restart.
Filename: "cmd.exe"; Parameters: "/c setx PATH ""{code:GetUpdatedPath}"""; Flags: runhidden

[Code]
function GetUpdatedPath(Param: string): string;
var
  CurrentPath: string;
begin
  RegQueryStringValue(HKCU, 'Environment', 'Path', CurrentPath);
  if CurrentPath <> '' then
    Result := CurrentPath + ';' + ExpandConstant('{app}')
  else
    Result := ExpandConstant('{app}');
end;

[Icons]
Name: "{autoprograms}\Artemis"; Filename: "{app}\artemis.exe"
