; =====================================================
; Script Inno Setup — Calculadora DAS
; Gera: "Calculadora DAS Setup.exe"
; =====================================================

[Setup]
AppName=Calculadora DAS
AppVersion=1.0.0
AppPublisher=Seu Nome ou Empresa
DefaultDirName={autopf}\Calculadora DAS
DefaultGroupName=Calculadora DAS
OutputBaseFilename=Calculadora DAS Setup
OutputDir=dist\installer
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

; Fecha o app se estiver aberto antes de instalar
CloseApplications=yes
; Reinicia o app automaticamente após instalar
RestartApplications=yes

; Ícone do instalador
SetupIconFile=das.ico

; Não precisa de direitos de administrador
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Área de Trabalho"; GroupDescription: "Ícones adicionais:"; Flags: unchecked

[Files]
; Arquivo principal gerado pelo PyInstaller
Source: "dist\Calculadora DAS.exe"; DestDir: "{app}"; Flags: ignoreversion

; Ícone e logo
Source: "das.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "das.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Atalho no menu Iniciar
Name: "{group}\Calculadora DAS"; Filename: "{app}\Calculadora DAS.exe"; IconFilename: "{app}\das.ico"

; Atalho na área de trabalho (opcional)
Name: "{autodesktop}\Calculadora DAS"; Filename: "{app}\Calculadora DAS.exe"; IconFilename: "{app}\das.ico"; Tasks: desktopicon

[Run]
; Abre o programa após instalar
Filename: "{app}\Calculadora DAS.exe"; Description: "Abrir Calculadora DAS"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
