# Nanobot (Enhanced Personal Version)

这是一个经过深度定制和增强的 Nanobot 版本，集成了更多实用的功能，使其更加强大和易于管理。

## ✨ 主要增强功能 (Key Features)

### 1. 🤖 Discord 机器人支持
除了原有的 Telegram 和 WhatsApp 支持外，本项目新增了完整的 **Discord** 集成。
- 支持在 Discord 频道中与 Nanobot 对话。
- 支持直接私信 (DM) 交互。
- 完整的图片/媒体消息处理。

### 2. 🧠 SiliconFlow (硅基流动) 模型支持
优化了对 SiliconFlow API 的支持，使其能够完美兼容 OpenAI 接口格式。
- 使用高性价比的国产大模型 (如 Qwen 2.5, DeepSeek 等)。
- 配置简单，只需在模型名称前加上 `openai/` 前缀即可。

### 3. 💬 WhatsApp 增强
- 修复并优化了 WhatsApp Web 的连接稳定性。
- 改进了二维码登录流程。

### 4. 🔄 自动重启与后台运行
为了让 Nanobot 能够作为长期在线的助手，我们增加了进程守护机制：
- **PowerShell 守护脚本**: 提供 `run_nanobot.ps1`，当程序崩溃时自动重启。
- **PM2 进程管理**: 支持使用 PM2 在后台运行，并配置 Windows 开机自启。

---

## 🛠️ 安装与配置 (Installation)

### 1. 获取代码
```bash
git clone https://github.com/ATCBK/Nanobot_new.git
cd Nanobot
pip install -e .
```

### 2. 初始化配置
首次运行需初始化配置文件：
```bash
nanobot onboard
```
配置文件通常位于 `~/.nanobot/config.json` (Windows 下为 `%USERPROFILE%\.nanobot\config.json`)。

### 3. 关键配置说明

#### SiliconFlow 模型配置
在 `config.json` 中配置 `llm` 部分：
```json
"llm": {
    "model": "openai/Qwen/Qwen2.5-72B-Instruct", 
    "api_key": "sk-your-siliconflow-key",
    "base_url": "https://api.siliconflow.cn/v1"
}
```
*注意：务必保留 `openai/` 前缀以确保兼容性。*

#### Discord 配置
在 `channels` 部分添加 `discord` 配置：
```json
"channels": {
    "discord": {
        "enabled": true,
        "token": "your-discord-bot-token",
        "allow_from": ["your-user-id"]
    },
    ...
}
```

---

## 🚀 启动方式 (Usage)

### 方式 A: 标准启动 (开发调试用)
```bash
python -m nanobot gateway
```

### 方式 B: 自动重启脚本 (推荐)
如果遇到网络波动导致程序退出，该脚本会自动重新拉起服务。
```powershell
.\run_nanobot.ps1
```

### 方式 C: PM2 后台运行与开机自启 (生产环境)
使用 PM2 让 Nanobot 在后台静默运行，并随系统启动。

1. **安装 PM2**:
   ```bash
   npm install -g pm2 pm2-windows-startup
   ```

2. **启动服务**:
   ```bash
   pm2 start --interpreter python --name nanobot "nanobot gateway"
   ```

3. **保存并设置开机自启**:
   ```bash
   pm2 save
   pm2-startup install
   ```

---

## 📂 项目结构变更
- `nanobot/channels/discord.py`: 新增 Discord 协议实现。
- `nanobot/config/schema.py`: 更新配置结构以支持 Discord。
- `run_nanobot.ps1`: 新增 PowerShell 自动重启脚本。
