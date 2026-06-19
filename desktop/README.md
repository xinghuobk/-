# ParaJudge 桌面端使用说明

> PyWebView + FastAPI 打包方案 · 适用于 Windows / macOS / Linux
> 版本：v0.1.0

---

## 一、架构概览

```
┌─────────────────────────────────────────────────────┐
│                  ParaJudge.exe (单一可执行)            │
│                                                     │
│  ┌──────────────┐         ┌──────────────────────┐  │
│  │ PyWebView    │  JS桥   │  FastAPI (uvicorn)   │  │
│  │ (WebView2)   │ ◄────► │  端口 127.0.0.1:8765  │  │
│  │ 渲染前端 UI  │         │  /api/parajudge/...  │  │
│  └──────────────┘         └──────────────────────┘  │
│       ▲                            ▲                │
│       │   python -m uvicorn        │                │
│       │   (子进程)                  │                │
└───────┼────────────────────────────┼────────────────┘
        │                            │
   操作系统 API              文件系统 / LLM API
   - 文件对话框               - arXiv / Crossref
   - 系统文件管理器            - OpenAI / Qwen
   - 默认应用打开
```

**核心设计**：

1. **进程模型**：桌面端启动器是主进程，FastAPI 后端是子进程（uvicorn）。关闭窗口时优雅 kill。
2. **通信**：
   - 前端 ↔ 后端：通过 HTTP + SSE（同 Web 部署）
   - 前端 ↔ Python 原生能力：通过 PyWebView 的 `window.pywebview.api` 桥
3. **打包**：PyInstaller 把 Python 解释器 + 所有依赖 + 前端资源打包到单一可执行文件。

---

## 二、目录结构

```
desktop/
├── main.py              # 启动入口（PyWebView + 子进程管理）
├── config.py            # 应用配置
├── server_runner.py     # uvicorn 子进程管理
├── bridge.py            # PyWebView JS-Python 桥
├── make_icon.py         # 图标生成脚本
├── ParaJudge.spec       # PyInstaller 打包配置
├── installer.nsi        # NSIS 安装脚本
├── run_dev.bat          # 开发模式启动
├── build.bat            # 打包为 dist/
├── build_installer.bat  # 进一步打包为 NSIS .exe 安装包
├── start.bat            # 一键启动（开发）
├── assets/
│   ├── icon.png
│   └── icon.ico
└── README.md            # 本文件
```

---

## 三、三种运行模式

### 1. 开发模式（推荐先用此模式调试）

```cmd
# Windows
desktop\run_dev.bat
# 或
python -m desktop.main
```

要求：
- 已安装 Python 3.10+
- 已 `pip install -r requirements.txt`
- 当前目录为项目根目录

### 2. 打包模式（绿色版）

```cmd
desktop\build.bat
```

产物：`dist\ParaJudge\ParaJudge.exe`（+ 依赖文件）
- 双击 `ParaJudge.exe` 即可运行
- **不需要安装 Python**
- 体积约 80-150 MB（含所有依赖）

### 3. 安装包模式（NSIS）

需要先安装 NSIS 3.0+：https://nsis.sourceforge.io/Download

```cmd
desktop\build.bat
desktop\build_installer.bat
```

产物：`dist\ParaJudge-Setup-0.1.0.exe`
- 标准 Windows 安装向导
- 自动创建开始菜单 + 桌面快捷方式
- 写入注册表（可正常卸载）
- 体积约 80-150 MB

---

## 四、配置项（环境变量）

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `PARAJUDGE_TITLE` | `ParaJudge · AI 多智能体辩论评估` | 窗口标题 |
| `PARAJUDGE_WIDTH` | `1400` | 窗口宽度 |
| `PARAJUDGE_HEIGHT` | `900` | 窗口高度 |
| `PARAJUDGE_PORT` | `8765` | 后端服务端口（注意不要与 8000 冲突） |
| `PARAJUDGE_GUI` | 自动 | 强制指定 GUI 后端（如 `edgechromium`） |
| `PARAJUDGE_DEBUG` | `0` | 设为 `1` 开启 webview 调试模式 |

在 `start.bat` 前设置：

```cmd
set PARAJUDGE_DEBUG=1
set PARAJUDGE_PORT=9000
desktop\start.bat
```

---

## 五、JS-Python 桥 API

前端通过 `window.Desktop.*` 调用原生能力（已封装在 `frontend/js/desktop-bridge.js`）。

### 5.1 文件操作

```javascript
// 选择本地文件
const r = await Desktop.openFile({
    title: '选择论文 PDF',
    fileTypes: 'PDF 文件 (*.pdf)|*.pdf',
});
if (r.ok) console.log('选中:', r.data);

// 保存文件
const r = await Desktop.saveFile({
    defaultFilename: 'report.md',
    fileTypes: 'Markdown (*.md)|*.md',
});
if (r.ok) console.log('保存到:', r.data);

// 用系统默认应用打开
await Desktop.openPath('C:\\Users\\me\\paper.pdf');

// 在文件管理器中显示
await Desktop.showInFolder('C:\\Users\\me\\paper.pdf');
```

### 5.2 导出裁决

```javascript
// 导出 JSON（自动判断桌面端/浏览器）
const result = await Desktop.exportVerdictJSON(fullPipelineOutput);
if (result.ok) {
    if (result.native) {
        console.log('已保存到:', result.path);
    } else {
        console.log('已通过浏览器下载');
    }
}
```

### 5.3 元信息

```javascript
const info = await Desktop.getAppInfo();
console.log(info);
// { name: 'ParaJudge', version: '0.1.0', platform: 'Windows-...',
//   backend_port: 8765, is_desktop: true, data_dir: 'C:\\Users\\me\\...' }
```

### 5.4 应用控制

```javascript
// 退出应用
await Desktop.quit();
```

---

## 六、环境降级

`Desktop.isDesktop` 自动判断环境：

| 运行环境 | 行为 |
| --- | --- |
| PyWebView 桌面端 | 调用原生 API（文件对话框、系统调用） |
| 普通浏览器 | 降级为 Web 下载（`<a download>`） |

无需在前端写环境判断代码，统一调用 `Desktop.xxx()` 即可。

---

## 七、跨平台说明

| 平台 | GUI 后端 | 打包工具 | 状态 |
| --- | --- | --- | --- |
| **Windows** | `edgechromium` (WebView2，需 Win10+) / `mshtml` (兼容) | PyInstaller → NSIS | ✅ 已验证 |
| **macOS** | `cocoa` (WebKit) | PyInstaller → .dmg | ✅ 需在 macOS 编译 |
| **Linux** | `gtk` (WebKitGTK) | PyInstaller → AppImage | ✅ 需在 Linux 编译 |

跨平台打包需要在对应平台上分别执行 `build.bat`（或对应的 `build.sh`）。

---

## 八、常见问题

### Q1: 启动时报错 "WebView2 not found"

Windows 10 1803 以下未预装 WebView2。两种解决：
1. 升级到 Windows 10 1803+（推荐）
2. 在 spec 中改用 `mshtml` 后端（兼容但功能弱）：
   ```python
   # ParaJudge.spec 的 a.scripts 中添加
   env["PARAJUDGE_GUI"] = "mshtml"
   ```

### Q2: 双击 exe 闪退

检查 `~/.parajudge/logs/desktop.log` 和 `backend.log` 的报错。

常见原因：
- 端口 8765 被占用 → 设置 `PARAJUDGE_PORT=9876`
- 缺少 VC++ 运行库 → 安装 Microsoft Visual C++ Redistributable

### Q3: 打包后体积太大

- 确认已开启 UPX 压缩（spec 中 `upx=True`）
- 检查 excludes 列表，可加入 `numpy`, `pandas` 等不需要的库
- 使用 `onedir` 模式（默认）而非 `onefile` —— 启动更快，体积相近

### Q4: 开发模式下后端启动慢

后端第一次启动会执行论文检索（Crossref / arXiv / Semantic Scholar），可能 2-5 秒。
可在 `server_runner.py` 中调小 `wait_ready` 超时。

---

## 九、调试技巧

### 桌面端调试

1. 设置 `PARAJUDGE_DEBUG=1` → PyWebView 打开 DevTools（F12）
2. 查看日志：`type %APPDATA%\ParaJudge\logs\parajudge.log`
3. 手动停止后端：`taskkill /F /IM uvicorn.exe`

### 后端独立调试

不启动桌面端，直接用浏览器调试：

```bash
# 终端 1：启动后端
uvicorn backend.api.server:app --port 8765 --reload

# 终端 2：浏览器
# 访问 http://localhost:8765/ui/index.html
```

前端会自动通过 `Desktop.isDesktop` 判断为浏览器模式。

---

## 十、发布清单

发布新版本时需要：

- [ ] 更新 `desktop/config.py` 中 `backend_port`（如需要）
- [ ] 重新生成图标（`python desktop/make_icon.py`）
- [ ] 执行 `desktop/build.bat`
- [ ] 在 Windows 10/11 上手动测试 `dist\ParaJudge\ParaJudge.exe`
- [ ] （可选）执行 `desktop\build_installer.bat` 生成安装包
- [ ] 上传到 GitHub Releases

---

## 十一、依赖清单

新增桌面端依赖（已加入 `requirements.txt` 或可选安装）：

```
pywebview>=5.0      # 主框架
pystray>=0.19       # 系统托盘（可选）
Pillow>=10.0        # 图标处理
pyinstaller>=6.0    # 打包工具
```

PyInstaller 仅在打包时需要，建议放入 `requirements-build.txt`。
