# swu-checkin

一个用于西南大学相关签到流程的自动化脚本项目。  
脚本入口为 `scripts/check_in.py`，仅通过环境变量读取账号密码：

- `SWU_USERNAME`
- `SWU_PASSWORD`

## 目录结构

```text
.
├── scripts/
│   ├── check_in.py
│   ├── get_info.py
│   ├── verify.py
│   └── des.py
├── requirements.txt
└── .github/workflows/swu-check.yml
```

## 环境要求

- Python 3.11（GitHub Actions 使用 3.11）
- 依赖：`requests`（见 `requirements.txt`）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 本地运行

### PowerShell（Windows）

```powershell
$env:SWU_USERNAME="你的学号"
$env:SWU_PASSWORD="你的密码"
python -u scripts/check_in.py
```

### Bash（Linux/macOS）

```bash
export SWU_USERNAME="你的学号"
export SWU_PASSWORD="你的密码"
python -u scripts/check_in.py
```

## GitHub Actions 自动运行

项目内已提供工作流：`.github/workflows/swu-check.yml`

- 每天北京时间 21:10 自动执行
- 支持 `workflow_dispatch` 手动触发

### 配置步骤

1. 打开仓库 `Settings` -> `Secrets and variables` -> `Actions`。
2. 新增以下 `Repository secrets`：
	- `SWU_USERNAME`
	- `SWU_PASSWORD`
3. 确认工作流已启用，在 `Actions` 页面可手动触发测试。

## 返回状态说明

`scripts/check_in.py` 会输出以下结果之一：

- `0`：今日暂无签到任务
- `1`：签到成功
- `2`：今日已签到，无需重复操作
- `3`：账号或密码验证失败
- `4`：连接错误或请求超时
- `5`：请假中，请检查是否有打卡任务

## 注意事项

- 脚本只从环境变量读取账号密码，不再支持手动输入。
- 建议通过 GitHub Secrets 存储敏感信息，不要把账号密码写入代码或提交到仓库。
- 若出现网络异常，可重试或稍后再执行。
