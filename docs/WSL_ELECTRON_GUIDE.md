# WSL 开发 Electron 应用最佳实践

## 核心挑战
WSL 本身是无头 (headless) Linux 环境，**不直接支持 GUI 窗口**。Electron 需要图形渲染层。

---

## 方案一：WSLg (推荐，Windows 11+)

Windows 11 自带 **WSLg** (Windows Subsystem for Linux GUI)，原生支持 Linux GUI 应用。

### 检查是否支持
```bash
# 检查 WSLg 是否可用
echo $DISPLAY
# 应该输出类似 :0 或 :0.0
```

### 启用 WSLg
```powershell
# 在 Windows PowerShell (管理员) 中：
wsl --update
wsl --shutdown
# 重新打开 WSL
```

### 运行 Electron
```bash
cd src/seabox
npm run dev
# 窗口应该会自动弹出
```

---

## 方案二：X Server (Windows 10 或 WSLg 不可用时)

### 步骤 1: 安装 X Server (Windows 端)
推荐 **VcXsrv** 或 **X410**:
- 下载 VcXsrv: https://sourceforge.net/projects/vcxsrv/
- 启动时选择 "Disable access control"

### 步骤 2: 配置 WSL DISPLAY 变量
```bash
# 添加到 ~/.bashrc
export DISPLAY=$(grep -m 1 nameserver /etc/resolv.conf | awk '{print $2}'):0.0
export LIBGL_ALWAYS_INDIRECT=1
```

### 步骤 3: 重启终端并运行
```bash
source ~/.bashrc
cd src/seabox
npm run dev
```

---

## 方案三：纯后端开发 + Windows 前端测试 (最稳定)

### 思路
- **WSL**: 运行 Python 后端 (`server.py`)
- **Windows**: 运行 Electron 前端

### 步骤
```bash
# WSL 终端 1: 启动 Python 后端
cd /home/dabah123/projects/caicai
.venv/bin/python src/seabox/api/server.py
# 后端运行在 localhost:8000
```

```powershell
# Windows PowerShell: 运行 Electron (需要 Windows 版 Node)
cd \\wsl$\Ubuntu\home\dabah123\projects\caicai\src\seabox
npm run dev
# 或者直接在 Windows 中 clone 项目
```

---

## 方案四：使用 Web 预览模式 (开发阶段推荐)

Vite 可以单独运行 Web 版本，无需 Electron 窗口：

```bash
cd src/seabox
# 仅运行 Web 服务 (不启动 Electron)
npx vite --host
# 然后在 Windows 浏览器中打开 http://localhost:5173
```

这样你可以：
1. 快速迭代 UI 代码
2. 使用浏览器 DevTools 调试
3. 无需解决 WSL GUI 问题

---

## 推荐工作流 (TDD + 分层测试)

```
┌─────────────────────────────────────────────────────────┐
│                    开发阶段                              │
├─────────────────────────────────────────────────────────┤
│ 1. 后端开发 (WSL)                                        │
│    pytest src/seabox/tests/test_api.py                  │
│                                                         │
│ 2. 前端开发 (WSL + 浏览器)                               │
│    npx vite --host  →  Windows 浏览器访问                │
│                                                         │
│ 3. 集成测试 (Windows 或 WSLg)                            │
│    npm run dev  →  完整 Electron 应用                   │
└─────────────────────────────────────────────────────────┘
```

---

## 常见问题

### GPU 错误
```bash
# 添加到 electron/main.ts (已完成)
app.disableHardwareAcceleration()
app.commandLine.appendSwitch('disable-gpu')
```

### 字体渲染问题
```bash
sudo apt install fonts-noto-cjk
```

### 找不到 libasound2
```bash
sudo apt install libasound2 libatk1.0-0 libcups2 libxss1 libxrandr2
```
