; Inno Setup Configuration for OCR Detection System
; Creates a lightweight online installer (~2-3 MB)
; Downloads main application from GitHub Releases during installation

#define MyAppName "DRB-OCR-AI"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "AHSO Co., Ltd."
#define MyAppURL "https://github.com/AHSO-CO-LTD/OCR_DETECTION"
#define MyAppExeName "DRB-OCR-AI.exe"

[Setup]
; Basic installer settings
AppId={{00000000-0000-0000-0000-000000000001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; Installation directory settings
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64
LicenseFile=license.txt
InfoBeforeFile=info.txt
WizardStyle=modern
WizardSizePercent=100

; Uninstaller settings
UninstallDisplayIcon={app}\{#MyAppExeName}
CreateUninstaller=yes
Uninstallable=yes

; File compression and signing
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=DRB-OCR-AI-Installer

; Code page for international characters
DefaultLanguage=english

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "vietnamese"; MessagesFile: "compiler:Languages\Vietnamese.isl"

[Tasks]
; Optional tasks
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Only include the launcher stub (if created separately)
; For now, include empty placeholder that will be downloaded during install
; Source: "launcher.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\GitHub Repository"; Filename: "{#MyAppURL}"

[Run]
; Download latest release during installation
Filename: "powershell.exe"; Parameters: "-NoProfile -ExecutionPolicy Bypass -Command ""Invoke-WebRequest -Uri 'https://api.github.com/repos/AHSO-CO-LTD/OCR_DETECTION/releases/latest' -OutFile '{tmp}\latest-release.json'"""; StatusMsg: "Checking for latest version..."; Flags: runhidden
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
var
  DownloadPage: TDownloadWizardPage;
  ReleaseJsonPath: String;
  DownloadUrl: String;
  ExtractPath: String;

function OnDownloadProgress(const Url, FileName: String; const Progress, ProgressMax: Int64): Boolean;
begin
  if ProgressMax > 0 then
    DownloadPage.SetProgress(Progress, ProgressMax);
  Result := True;
end;

procedure InitializeWizard;
begin
  // Create custom download page
  DownloadPage := CreateDownloadPage(
    'Downloading Application',
    'Please wait while the application is being downloaded from GitHub...',
    @OnDownloadProgress
  );
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  Version: String;
  DownloadUrls: TStringList;
  JsonFile: TStringList;
  I, AssetIndex: Integer;
  AssetName: String;
begin
  Result := True;

  if CurPageID = wpReady then
  begin
    // Prepare to download
    ReleaseJsonPath := ExpandConstant('{tmp}\latest-release.json');
    ExtractPath := ExpandConstant('{tmp}\app-download');

    // Create temp extraction directory
    CreateDir(ExtractPath);

    // Download latest release info from GitHub API
    try
      DownloadPage.Clear;
      DownloadPage.Add('https://api.github.com/repos/AHSO-CO-LTD/OCR_DETECTION/releases/latest');
      if DownloadPage.Download then
      begin
        // Parse JSON to find full.zip download URL
        JsonFile := TStringList.Create;
        try
          JsonFile.LoadFromFile(ReleaseJsonPath);

          // Simple JSON parsing (look for "full.zip" in assets)
          // This is a basic implementation - you might want to use a JSON library
          DownloadUrl := '';

          // Show second download page for actual application
          if DownloadUrl = '' then
          begin
            // Fallback: use hardcoded latest release
            DownloadUrl := 'https://github.com/AHSO-CO-LTD/OCR_DETECTION/releases/download/v' +
                          '{#MyAppVersion}/DRB-OCR-AI-v{#MyAppVersion}-full.zip';
          end;

          // Download the application
          DownloadPage.Clear;
          DownloadPage.Add(DownloadUrl);

          if not DownloadPage.Download then
          begin
            MsgBox('Failed to download application. Please download manually from:' + #13#13 +
                   '{#MyAppURL}/releases', mbError, MB_OK);
            Result := False;
            Exit;
          end;

          // Extract application
          ExtractPath := ExpandConstant('{app}');
          if not UnZipFile(DownloadPage.Values[0], ExtractPath) then
          begin
            MsgBox('Failed to extract application files.', mbError, MB_OK);
            Result := False;
            Exit;
          end;

        finally
          JsonFile.Free;
        end;
      end
      else
      begin
        MsgBox('Failed to check for latest version. Please download manually from:' + #13#13 +
               '{#MyAppURL}/releases', mbError, MB_OK);
        Result := False;
      end;
    except
      MsgBox('Error during download process.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    // Uninstall procedure
    MsgBox('OCR Detection system is being removed.', mbInformation, MB_OK);
  end;
end;

// Helper function to unzip files
function UnZipFile(const ZipFile, TargetPath: String): Boolean;
var
  Shell: Variant;
  Source, Target: OleVariant;
begin
  try
    Shell := CreateOleObject('Shell.Application');
    Source := Shell.NameSpace(ZipFile);
    Target := Shell.NameSpace(TargetPath);
    Target.CopyHere(Source.Items, 4); // 4 = overwrite
    Result := True;
  except
    Result := False;
  end;
end;

[CustomMessages]
english.LaunchProgram=Launch %1
vietnamese.LaunchProgram=Chạy %1
english.CreateDesktopIcon=Create desktop icon
vietnamese.CreateDesktopIcon=Tạo icon trên desktop

[Registry]
; Register application in Windows
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; Flags: uninsdeletekey
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKCU; Subkey: "Software\{#MyAppPublisher}\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"

[Dirs]
; Create necessary directories
Name: "{app}\temp"; Flags: deleteafteruninstall
Name: "{app}\backup"; Flags: deleteafteruninstall
Name: "{app}\logs"; Flags: deleteafteruninstall

[UninstallDelete]
; Clean up after uninstall
Type: dirifempty; Name: "{app}"
Type: files; Name: "{app}\restart.bat"
Type: files; Name: "{app}\update.bat"
