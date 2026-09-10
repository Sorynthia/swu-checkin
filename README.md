# SWU 查寝打卡脚本

西南大学钉钉查寝自动打卡独立脚本。适用于需要在本地或云函数中运行自动打卡的场景。

## 功能特性

- ✅ 自动获取当日打卡任务
- ✅ 支持统一身份认证登录
- ✅ OCR 自动识别验证码
- ✅ 自动填写宿舍信息和位置
- ✅ 支持请假状态检测
- ✅ 防重复打卡
- ✅ 详细状态码返回
- ✅ GitHub Actions 定时任务
- ✅ 失败邮件通知

## 环境要求

- Python 3.13+
- 依赖库：requests, beautifulsoup4, Pillow, ddddocr

## 快速开始

### 方式一：GitHub Actions 自动签到（推荐）

无需本地环境，全自动云端执行：

1. Fork 本仓库到你的账号
2. 在仓库 **Settings** → **Secrets** 中配置账号密码
3. 每天 21:30 自动签到

**详细配置教程**: [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)

### 方式二：本地运行

#### 1. 安装依赖

```bash
# 使用 pip
pip install -e .

# 或使用 uv（推荐）
uv sync
```

#### 2. 运行脚本

安装后可直接使用命令行工具：

```bash
# 设置环境变量后运行
export SWUDK_USERNAME="你的学号"
export SWUDK_PASSWORD="你的密码"
swu-checkin
```

或作为 Python 模块调用：

```python
from swu_checkin import check_in

# 从环境变量读取账号密码
check_in()
```

##### Windows PowerShell

```powershell
$env:SWUDK_USERNAME="你的学号"
$env:SWUDK_PASSWORD="你的密码"
swu-checkin
```

##### Linux / macOS

```bash
export SWUDK_USERNAME="你的学号"
export SWUDK_PASSWORD="你的密码"
swu-checkin
```

## 返回状态码

| 状态码 | 含义 |
|-------|------|
| 0 | 今日暂无签到任务 |
| 1 | 签到成功 |
| 2 | 今日已签到，无需重复操作 |
| 3 | 账号或密码验证失败 |
| 4 | 连接错误或请求超时 |
| 5 | 请假中，跳过打卡 |

## 项目结构

```
.
├── .github/
│   └── workflows/
│       └── checkin.yml       # GitHub Actions 工作流
├── src/
│   └── swu_checkin/
│       ├── __init__.py
│       ├── check_in.py       # 主打卡脚本
│       ├── get_info.py       # 信息获取模块
│       ├── verify.py         # 登录验证模块
│       ├── identity.py       # 身份选择处理
│       └── des.py            # DES 加密工具
├── pyproject.toml            # 项目配置和依赖
├── README.md
└── GITHUB_ACTIONS.md         # Actions 配置指南
```

## 工作流程

1. 使用校园网账号密码登录统一身份认证
2. 通过 OCR 识别验证码自动登录
3. 获取 token 和打卡任务信息
4. 检测请假状态
5. 自动填写宿舍位置信息并提交打卡

## 注意事项

- ⚠️ 脚本仅从环境变量读取账号密码
- ⚠️ 切勿将账号密码写入代码或提交到仓库
- ⚠️ 建议在正式使用前先手动测试一次
- ⚠️ 网络异常时可重试或稍后执行
- ⚠️ GitHub Actions 使用 Secrets 存储敏感信息，安全可靠

## 相关项目

- **[swu-login](https://github.com/Sorynthia/swu-login)** - 西南大学统一身份认证独立登录模块
- **[swudk-dingtalk](https://github.com/Sorynthia/swudk-dingtalk)** - 钉钉扫码打卡前端工具

## 贡献指南

欢迎提交 Issue 和 Pull Request！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

## 引用与归属

如果你在项目中使用或参考了本代码，建议按以下方式标注：

```
基于 Sorynthia/swu-checkin 开发
GitHub: https://github.com/Sorynthia/swu-checkin
```

本项目采用 MIT 许可证，欢迎使用和修改，但请保留原作者信息。

## 许可证

MIT License
