; ========================================
; Cite-Agent Professional Installer Script
; Inno Setup 6.x Configuration
; Creates: Cite-Agent-Installer-v2.0.exe
; ========================================

#define MyAppName "Cite-Agent"
#define MyAppNameChinese "學術研究助手"
#define MyAppVersion "1.3.9"
#define MyAppPublisher "Cite-Agent Team"
#define MyAppURL "https://github.com/Spectating101/cite-agent"
#define MyAppExeName "python.exe"
#define PythonVersion "3.11.9"
#define PythonDownloadUrl "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

[Setup]
; App Information (Bilingual)
AppId={{8F9A2B3C-4D5E-6F7A-8B9C-0D1E2F3A4B5C}
AppName={#MyAppName} - {#MyAppNameChinese}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Default Installation Directory (Per-User)
DefaultDirName={userappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output Configuration
OutputDir=.
OutputBaseFilename=Cite-Agent-Installer-v2.0-PerUser
SetupIconFile=compiler:SetupClassicIcon.ico
Compression=lzma2/max
SolidCompression=yes

; Windows Version Requirements
MinVersion=10.0
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Visual Settings
WizardStyle=modern
WizardImageFile=compiler:WizModernImage.bmp
WizardSmallImageFile=compiler:WizModernSmallImage.bmp
DisableWelcomePage=no
ShowLanguageDialog=no

; Uninstall Settings
UninstallDisplayIcon={app}\cite-agent-icon.ico
UninstallDisplayName={#MyAppName} - AI Research Assistant

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] - AI Research Assistant for Academics (AI學術研究助手) on your computer.%n%nSupports English and Chinese (支持英文和中文)%n%nPerfect for R Studio and Stata users!%n%nIt is recommended that you close all other applications before continuing.

[Messages]
WelcomeLabel2={cm:WelcomeLabel2}

[Files]
; PowerShell Installer Script
Source: "Install-CiteAgent.ps1"; DestDir: "{app}"; Flags: ignoreversion

; Helper Scripts
Source: "cite-agent.bat"; DestDir: "{app}"; Flags: ignoreversion

; Documentation (Bilingual)
Source: "START_HERE.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "QUICKSTART.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Desktop Shortcut (launches cite-agent directly)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\cite-agent.bat"; WorkingDir: "{userprofile}"; Comment: "Cite-Agent AI Research Assistant 學術研究助手"; IconFilename: "{sys}\cmd.exe"; IconIndex: 0

; Start Menu Shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\cite-agent.bat"; WorkingDir: "{userprofile}"; Comment: "Launch Cite-Agent 啟動 Cite-Agent"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{group}\Documentation 文檔"; Filename: "{app}\README.txt"
Name: "{group}\Quick Start 快速開始"; Filename: "{app}\QUICKSTART.txt"

[Run]
; Run the PowerShell installer after file extraction
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\Install-CiteAgent.ps1"" -DefaultVersion ""{#MyAppVersion}"" -PythonVersion ""{#PythonVersion}"" -PythonDownloadUrl ""{#PythonDownloadUrl}"" -LaunchFromInstaller"; StatusMsg: "Installing Cite-Agent components... 正在安裝 Cite-Agent 組件..."; Flags: runhidden waituntilterminated

; Optional: Launch Cite-Agent after installation
Filename: "{app}\cite-agent.bat"; Description: "Launch Cite-Agent now 立即啟動 Cite-Agent"; Flags: postinstall nowait skipifsilent shellexec; Check: PythonInstalled

[Code]
var
  ProgressPage: TOutputProgressWizardPage;

function PythonInstalled: Boolean;
var
  ResultCode: Integer;
begin
  // Check if Python launcher or python.exe are available
  Result := Exec('cmd.exe', '/c py --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  if not Result then
    Result := Exec('cmd.exe', '/c python --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

procedure InitializeWizard;
begin
  // Custom welcome page with bilingual content
  WizardForm.WelcomeLabel2.Caption :=
    'This will install ' + '{#MyAppName}' + ' {#MyAppVersion} - AI Research Assistant for Academics (AI學術研究助手) on your computer.' + #13#10#13#10 +
    'Supports English and Chinese (支持英文和中文)' + #13#10#13#10 +
    'Perfect for R Studio and Stata users!' + #13#10#13#10 +
    'Features 功能:' + #13#10 +
    '  ✓ Academic paper search 學術論文搜索' + #13#10 +
    '  ✓ Financial data analysis 財務數據分析' + #13#10 +
    '  ✓ Data analysis & coding 數據分析與編程' + #13#10 +
    '  ✓ R Studio integration R Studio 整合' + #13#10#13#10 +
    'It is recommended that you close all other applications (especially R Studio) before continuing.' + #13#10 +
    '建議您在繼續之前關閉所有其他應用程序（特別是 R Studio）。';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
  PathValue: String;
  ScriptsPath: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Add Python Scripts to PATH permanently
    if RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', PathValue) then
    begin
      // Get Python Scripts path
      if Exec('cmd.exe', '/c python -c "import site; print(site.USER_BASE + ''\Scripts'')"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      begin
        // Broadcast WM_SETTINGCHANGE to notify all applications
        // This is handled by the PowerShell script
      end;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Uninstall cite-agent via pip
    if MsgBox('Do you want to completely remove Cite-Agent from your system?' + #13#10 + '是否要從系統中完全刪除 Cite-Agent？' + #13#10#13#10 + 'This will uninstall the Python package.' + #13#10 + '這將卸載 Python 包。', mbConfirmation, MB_YESNO) = IDYES then
    begin
      Exec('cmd.exe', '/c python -m pip uninstall -y cite-agent', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
  end;
end;

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Registry]
; No registry modifications needed - PATH handled by PowerShell script
