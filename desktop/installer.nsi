; ============================================================
; ParaJudge Desktop - NSIS 安装脚本
; 需要 NSIS 3.0+：https://nsis.sourceforge.io/Download
; 编译：makensis installer.nsi
; ============================================================

!include "MUI2.nsh"
!include "LogicLib.nsh"

!define APPNAME "ParaJudge"
!define COMPANYNAME "ParaJudge Lab"
!define DESCRIPTION "AI 多智能体辩论评估系统"
!define VERSION "0.1.0"

Name "${APPNAME} ${VERSION}"
OutFile "ParaJudge-Setup-${VERSION}.exe"
InstallDir "$PROGRAMFILES64\${APPNAME}"
InstallDirRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}" "InstallDir"
RequestExecutionLevel admin
ShowInstDetails show

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

Section "主程序" SecMain
    SetOutPath "$INSTDIR"

    ; 复制整个应用目录
    File /r "ParaJudge\*.*"

    ; 创建桌面快捷方式
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\ParaJudge.exe"
    CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\ParaJudge.exe"

    ; 写入注册表（用于卸载）
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${COMPANYNAME}\${APPNAME}" "Version" "${VERSION}"

    ; 卸载程序
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
SectionEnd

Section "Uninstall"
    RMDir /r "$INSTDIR"
    RMDir /r "$SMPROGRAMS\${APPNAME}"
    Delete "$DESKTOP\${APPNAME}.lnk"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    DeleteRegKey HKLM "Software\${COMPANYNAME}\${APPNAME}"
SectionEnd
