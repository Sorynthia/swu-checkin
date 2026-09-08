# SWU 查寝打卡脚本

西南大学钉钉查寝自动打卡脚本，使用校园网账号密码登录。

## 功能特性

- ✅ 自动获取当日打卡任务
- ✅ 自动填写宿舍信息和位置
- ✅ 支持请假状态检测
- ✅ 防重复打卡
- ✅ 详细状态码返回

## 环境要求

- Python 3.13+
- 依赖库：requests, beautifulsoup4, Pillow, ddddocr

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
│   ├── get_info.py       # 信息获取模块（token、学号、宿舍信息）
│   ├── verify.py         # 登录验证模块
│   ├── identity.py       # 身份选择处理
│   └── des.py            # DES 加密工具
├── pyproject.toml        # 项目配置和依赖
└── README.md
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

## 更新日志

### 2026.9.8
- 简化为核心打卡功能，移除钉钉扫码等额外模块
- 迁移到 pyproject.toml 管理依赖
- 适配 Python 3.13
- 完善文档结构

### 2026.4.10
- 修复官方登录接口变化

## 相关项目

- [SWUDK 后端服务](https://github.com/Sorynthia/swudk) - 完整的查寝打卡管理系统

## 许可证

MIT License
