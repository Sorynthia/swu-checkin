# SWU 查寝打卡脚本

西南大学钉钉查寝自动打卡脚本，支持本地运行和 GitHub Actions 定时任务。

## 功能特性

- ✅ 自动获取当日打卡任务
- ✅ 自动填写宿舍信息和位置
- ✅ 支持请假状态检测
- ✅ 防重复打卡
- ✅ 详细状态码返回

## 环境要求

- Python 3.13+
- 依赖库：requests, beautifulsoup4, Pillow, ddddocr, qrcode

## 快速开始

### 1. 安装依赖

```bash
# 使用 pip
pip install -e .

# 或使用 uv（推荐）
uv sync
```

### 2. 本地运行

#### Windows PowerShell

```powershell
$env:SWUDK_USERNAME="你的学号"
$env:SWUDK_PASSWORD="你的密码"
python scripts/check_in.py
```

#### Linux / macOS

```bash
export SWUDK_USERNAME="你的学号"
export SWUDK_PASSWORD="你的密码"
python scripts/check_in.py
```

### 3. GitHub Actions 自动打卡（可选）

1. Fork 本仓库到你的 GitHub 账号
2. 进入仓库 **Settings** → **Secrets and variables** → **Actions**
3. 添加以下 Repository secrets：
   - SWUDK_USERNAME：你的学号
   - SWUDK_PASSWORD：你的密码
4. 创建 .github/workflows/checkin.yml 工作流文件
5. 脚本将按配置时间自动运行

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
├── scripts/
│   ├── check_in.py       # 主打卡脚本
│   ├── get_info.py       # 信息获取模块
│   ├── verify.py         # 登录验证模块
│   ├── dingding.py       # 钉钉扫码登录
│   ├── swu_login.py      # 校园网统一认证
│   ├── identity.py       # 身份验证
│   ├── des.py            # DES 加密工具
│   └── new.py            # 新版本适配
├── pyproject.toml        # 项目配置和依赖
└── README.md
```

## 开发

项目使用 pyproject.toml 管理依赖和配置：

```bash
# 安装开发依赖
uv sync

# 代码格式化
ruff format .

# 代码检查
ruff check .
```

## 注意事项

- ⚠️ 脚本仅从环境变量读取账号密码，不支持手动输入
- ⚠️ 请通过 GitHub Secrets 管理敏感信息，切勿将账号密码写入代码
- ⚠️ 建议在正式使用前先手动测试一次
- ⚠️ 网络异常时可重试或稍后执行

## 更新日志

### 2026.9.8
- 迁移到 pyproject.toml 管理依赖
- 适配 Python 3.13
- 适配 SWUDK 后端脚本
- 移除 GitHub Actions 工作流（由用户自行配置）
- 完善文档结构

### 2026.4.10
- 修复官方登录接口变化

## 相关项目

- [SWUDK 后端服务](https://github.com/Sorynthia/swudk) - 完整的查寝打卡管理系统

## 许可证

MIT License
