# GitHub Actions 自动签到配置指南

## 功能说明

- **自动签到**: 每天北京时间 21:30 自动执行签到
- **手动触发**: 支持在 GitHub Actions 页面手动运行
- **失败通知**: 签到失败时自动发送邮件通知

---

## 配置步骤

### 1. 配置 GitHub Secrets

进入仓库页面: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

添加以下 secrets（⚠️ 不要提交到代码里）:

#### 必需配置

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| SWU_USERNAME | 校园网账号 | 2021xxxxxx |
| SWU_PASSWORD | 校园网密码 | your_password |

#### 邮件通知配置（可选）

如果需要签到失败时收到邮件通知，添加以下配置：

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| MAIL_SERVER | SMTP 服务器地址 | smtp.gmail.com / smtp.qq.com |
| MAIL_PORT | SMTP 端口 | 587 (TLS) 或 465 (SSL) |
| MAIL_USERNAME | 发件邮箱账号 | your_email@gmail.com |
| MAIL_PASSWORD | 邮箱授权码（不是登录密码） | xxxx xxxx xxxx xxxx |
| NOTIFY_EMAIL | 接收通知的邮箱 | your_email@qq.com |

---

## 常见邮箱配置

### QQ 邮箱
```
MAIL_SERVER: smtp.qq.com
MAIL_PORT: 587
MAIL_USERNAME: your_qq@qq.com
MAIL_PASSWORD: 授权码（在 QQ 邮箱设置 → 账户 → 开启 SMTP 服务获取）
```

### Gmail
```
MAIL_SERVER: smtp.gmail.com
MAIL_PORT: 587
MAIL_USERNAME: your_email@gmail.com
MAIL_PASSWORD: 应用专用密码（在 Google 账户安全设置中生成）
```

### 163 邮箱
```
MAIL_SERVER: smtp.163.com
MAIL_PORT: 465
MAIL_USERNAME: your_email@163.com
MAIL_PASSWORD: 授权码（在邮箱设置 → POP3/SMTP/IMAP 中开启）
```

### Outlook
```
MAIL_SERVER: smtp-mail.outlook.com
MAIL_PORT: 587
MAIL_USERNAME: your_email@outlook.com
MAIL_PASSWORD: 邮箱密码或应用密码
```

---

## 使用说明

### 自动运行
配置完成后，Actions 会在每天 21:30 自动执行。

### 手动触发
1. 进入仓库 **Actions** 页面
2. 选择 **自动签到** workflow
3. 点击 **Run workflow** → **Run workflow**

### 查看日志
**Actions** → 选择运行记录 → 查看详细日志

---

## 修改执行时间

编辑 `.github/workflows/checkin.yml`:

```yaml
schedule:
  # cron 格式: 分 时 日 月 周
  # 北京时间 = UTC + 8
  - cron: '30 13 * * *'  # 北京时间 21:30
```

常用时间：
- 每天 21:00: `0 13 * * *`
- 每天 22:00: `0 14 * * *`
- 每天 23:00: `0 15 * * *`

---

## 安全说明

✅ **安全实践**:
- 所有敏感信息存储在 GitHub Secrets，加密存储
- Secrets 不会出现在日志中
- 代码仓库中不包含任何凭证

⚠️ **注意事项**:
- 不要在公开 Issue/PR 中提及凭证
- 定期更新密码和授权码
- 如果仓库变为公开，重新检查 Secrets 配置

---

## 故障排查

### 签到失败
1. 检查 Actions 日志中的错误信息
2. 验证 SWU_USERNAME 和 SWU_PASSWORD 是否正确
3. 手动运行测试: `python -m swu_checkin.check_in`

### 邮件未收到
1. 检查垃圾邮件文件夹
2. 验证 SMTP 配置是否正确
3. 确认授权码而非登录密码
4. 查看 Actions 日志中的邮件发送错误

### Actions 未执行
1. 检查仓库是否启用了 Actions
2. 确认工作流文件路径: `.github/workflows/checkin.yml`
3. 验证 cron 表达式格式

---

## 禁用自动签到

### 临时禁用
**Actions** → **自动签到** → **Disable workflow**

### 永久删除
删除文件: `.github/workflows/checkin.yml`
