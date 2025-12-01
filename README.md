# Gemini Enterprise 自动注册工具

## 📌 项目简介

这是一个基于 Python 与 DrissionPage 的 Gemini Enterprise 自动注册工具，用于批量或快速完成 Gemini Enterprise 账号的注册流程。工具从生成随机邮箱、打开注册页面、填写表单到读取验证码并提交，尽可能模拟人工操作，降低人工介入成本。

### ✨ 核心功能

- ✅ 自动生成随机邮箱地址（支持自定义域名）
- ✅ 自动访问 Gemini Enterprise 注册页面
- ✅ 自动填写邮箱并提交
- ✅ 支持两种验证码获取方式：
  - tempmail.plus API（推荐，更快更稳定）
  - IMAP/POP3 邮箱收取（适用于自建邮箱服务器）
- ✅ 自动填写验证码和姓名
- ✅ 完成整个注册流程
- ✅ 多语言提示与日志输出
- ✅ 自动生成过程截图

## 🚀 快速开始

### 1. 环境要求

- Python 3.9+
- Chrome/Chromium/Edge 浏览器
- 可用的邮箱域名和验证码接收方式

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

**重要：首次使用请按以下步骤配置**

1. 将 `.env.example` 复制为 `.env`：
   ```bash
   # Windows
   copy .env.example .env
   
   # Linux/macOS
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，填写您的实际配置：

#### 必填配置项

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `DOMAIN` | 邮箱域名 | `storm-brewing.shop` |
| `TEMP_MAIL` | tempmail.plus 用户名<br/>（不使用则设为 `null`） | `your_username` 或 `null` |
| `TEMP_MAIL_EPIN` | tempmail.plus 的 epin | `123456` |
| `TEMP_MAIL_EXT` | 临时邮箱后缀 | `@mailto.plus` |

#### IMAP/POP3 配置（当 TEMP_MAIL=null 时）

| 配置项 | 说明 | 示例 |
|--------|------|------|
| `IMAP_PROTOCOL` | 协议类型 | `IMAP` 或 `POP3` |
| `IMAP_SERVER` | 服务器地址 | `imap.gmail.com` |
| `IMAP_PORT` | 服务器端口 | `993`（IMAP SSL）<br/>`995`（POP3 SSL） |
| `IMAP_USER` | 邮箱账号 | `your@email.com` |
| `IMAP_PASS` | 邮箱密码或授权码 | Gmail/QQ邮箱需使用授权码 |
| `IMAP_DIR` | 收件箱目录名 | `inbox` 或 `INBOX` |

#### 可选配置项

| 配置项 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `BROWSER_HEADLESS` | 无头模式（后台运行） | `false` | `true` 或 `false` |
| `BROWSER_PROXY` | HTTP 代理 | 无 | `http://127.0.0.1:7890` |
| `BROWSER_PATH` | 自定义浏览器路径 | 系统默认 | Windows: `C:/Program Files/Google/Chrome/Application/chrome.exe`<br/>macOS: `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` |
| `BROWSER_USER_AGENT` | 自定义 User-Agent | 浏览器默认 | 自定义 UA 字符串 |

⚠️ **注意事项**
- 使用 IMAP/POP3 时，部分邮箱（如 Gmail、QQ 邮箱）需开启"客户端授权"并使用专用密码
- 目录名需与 `IMAP_DIR` 配置一致
- `.env` 文件包含敏感信息，已被 Git 忽略，请勿提交到版本库

### 4. 运行工具

```bash
python gemini_auto_register.py
```

运行后，工具会：
1. 加载配置并校验必要字段
2. 启动浏览器并访问注册页面
3. 生成随机邮箱和密码
4. 自动填写并提交表单
5. 获取验证码并完成注册
6. 保存日志和截图

### 5. 构建可执行文件（可选）

如需打包为独立可执行文件，方便在无 Python 环境的机器上运行：

```bash
python build.py
```

生成的文件位于 `dist/` 目录：
- Windows: `dist/windows/`
- macOS: `dist/mac/`
- Linux: `dist/linux/`

打包后的程序会自动复制 `.env.example` 文件，使用前需按照上述步骤配置 `.env`。

## 📁 项目结构

```
├── gemini_auto_register.py   # 主程序入口
├── get_email_code.py          # 验证码获取模块
├── browser_utils.py           # 浏览器配置与管理
├── config.py                  # 环境变量加载与校验
├── language.py                # 多语言支持
├── logger.py                  # 日志模块
├── build.py                   # PyInstaller 打包脚本
├── names-dataset.txt          # 随机姓名词库
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量示例
├── .gitignore                 # Git 忽略规则
├── LICENSE                    # 许可证文件
└── README.md                  # 本文档
```

## 📝 运行流程

1. **加载配置**：读取 `.env`，校验必要字段（域名、临时邮箱或 IMAP 账号等）
2. **初始化浏览器**：按配置设置 UA、代理、无头模式及可选的浏览器路径
3. **生成账号信息**：从词库随机生成姓名，拼接时间戳构造邮箱，生成随机密码
4. **访问注册页并填写表单**：点击开始使用和开始试用，输入邮箱并提交
5. **获取验证码**：调用 tempmail.plus API 或 IMAP/POP3 收件箱，提取验证码
6. **提交验证码与姓名**：自动填入验证码并提交；随后填写姓名并完成创建
7. **结果判断**：根据最终 URL 判定成功；全程保存日志和截图

## 📊 日志与截图

- **日志文件**：保存在 `logs/YYYY-MM-DD.log`，包含运行信息与错误详情
- **截图文件**：保存在 `screenshots/`，记录关键步骤（按钮点击、验证码输入、最终页面等）

## ❓ 常见问题

### Q: 提示"配置文件 .env 未找到"
**A:** 请按照"快速开始"章节的步骤 3，将 `.env.example` 复制为 `.env` 并填写配置。

### Q: 验证码获取失败
**A:** 
- 如使用 tempmail.plus，请检查 `TEMP_MAIL_EPIN` 是否正确
- 如使用 IMAP/POP3，请确认服务器地址、端口、账号密码正确，并已开启客户端授权

### Q: 浏览器无法启动
**A:** 
- 检查是否安装了 Chrome/Chromium/Edge 浏览器
- 如需指定自定义浏览器，请配置 `BROWSER_PATH`

### Q: 注册过程中页面加载失败
**A:** 
- 检查网络连接是否正常
- 如访问受限，请配置 `BROWSER_PROXY` 使用代理

### Q: 打包后的程序无法运行
**A:** 
- 确保在程序目录下创建了 `.env` 文件
- 检查 `.env` 配置是否正确

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

- **报告问题**：请在 GitHub Issues 中详细描述问题和复现步骤
- **提交代码**：请确保代码符合项目风格，并通过基本测试
- **改进文档**：发现文档错误或不清晰的地方，欢迎提出改进建议

## 📄 许可证声明

本项目采用 [CC BY-NC-ND 4.0](https://creativecommons.org/licenses/by-nc-nd/4.0/) 许可证。

这意味着您可以：
- ✅ **分享** — 在任何媒介以任何形式复制、发行本作品

但必须遵守以下条件：
- **署名（BY）**：您必须给出适当的署名，提供指向本许可证的链接，同时标明是否作了修改
- **非商业性使用（NC）**：您不得将本作品用于商业目的
- **禁止演绎（ND）**：您不得修改、转换或以本作品为基础进行创作

完整许可证文本请查看 [LICENSE](./LICENSE) 文件。

## ⚠️ 免责声明

- 本项目仅供学习交流使用，请勿用于商业用途
- 本项目不承担任何法律责任，使用本项目造成的任何后果，由使用者自行承担
- 请遵守相关服务条款和当地法律法规

## 📚 第三方资源说明

- **names-dataset.txt**：用于生成随机姓名的词库文件。此文件包含常见英文姓名数据，来源于公开数据集，仅用于生成测试用邮箱前缀和展示名，不涉及敏感信息。

## 📮 联系方式

如有问题或建议，请通过 GitHub Issues 联系。

---

**祝使用愉快！** 🎉
