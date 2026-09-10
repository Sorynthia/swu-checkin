# GitHub Actions 自动签到配置指南

## 功能说明

- **自动签到**: 每天北京时间 21:30 自动执行签到
- **手动触发**: 支持在 GitHub Actions 页面手动运行
- **智能通知**: 签到异常时自动发送详细邮件通知
- **详细日志**: 完整记录每步执行情况，便于排查问题
- **开关控制**: 默认关闭，需要手动启用

---

## 快速开始

### 第一步：启用自动签到

1. 进入仓库主页
2. 打开文件：`.github/workflows/checkin.yml`
3. 点击右上角 **编辑按钮**（铅笔图标）
4. 找到第 7 行，将 `ENABLED: false` 改为 `ENABLED: true`
5. 点击 **Commit changes** 提交

```yaml
# 修改前
env:
  ENABLED: false  # 默认关闭

# 修改后
env:
  ENABLED: true   # 启用自动签到
```

### 第二步：配置账号密码

进入仓库页面: **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

添加以下 secrets（⚠️ 不要提交到代码里）:

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| SWU_USERNAME | 校园网账号 | 2021xxxxxx |
| SWU_PASSWORD | 校园网密码 | your_password |

### 第三步：配置邮件通知（可选）

如果需要签到异常时收到邮件通知，继续添加以下配置：

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| MAIL_SERVER | SMTP 服务器地址 | smtp.gmail.com / smtp.qq.com |
| MAIL_PORT | SMTP 端口 | 587 (TLS) 或 465 (SSL) |
| MAIL_USERNAME | 发件邮箱账号 | your_email@gmail.com |
| MAIL_PASSWORD | 邮箱授权码（不是登录密码） | xxxx xxxx xxxx xxxx |
| NOTIFY_EMAIL | 接收通知的邮箱 | your_email@qq.com |

---

## 邮件通知规则

### 正常情况（不发邮件）
- ✅ `[1]` 签到成功
- ✅ `[2]` 已签到

### 异常情况（自动发邮件）
- ⚠️ `[0]` 今日无签到记录
- ❌ `[3]` 登录失败（账号密码错误）
- ❌ `[4]` 网络错误或数据异常
- ℹ️ `[5]` 请假期间无需签到

邮件包含状态码、详细原因和处理建议。

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
启用后，Actions 会在每天 21:30 自动执行。

### 手动触发
1. 进入仓库 **Actions** 页面
2. 选择 **自动签到** workflow
3. 点击 **Run workflow** → **Run workflow**

### 查看日志

**Actions** → 选择运行记录 → 查看详细日志

日志包含：
- 依赖安装过程
- 签到执行时间和账号（脱敏）
- 详细签到结果
- 状态码和状态信息
- 邮件发送状态

---

## 日志示例

### 未启用时
```
=========================================
⚠️  自动签到未启用
=========================================

如需启用自动签到，请编辑 .github/workflows/checkin.yml
将 ENABLED 改为 true

步骤：
1. 进入仓库主页
2. 打开 .github/workflows/checkin.yml
3. 点击编辑按钮
4. 将 'ENABLED: false' 改为 'ENABLED: true'
5. 提交更改

=========================================
```

### 成功签到
```
=========================================
开始执行签到任务
时间: 2024-01-15 21:30:15
账号: 2021****23
=========================================

=========================================
签到结果
=========================================
[1] 签到成功

=========================================
状态码: 1
状态信息: 签到成功
退出码: 0
=========================================

✅ 签到正常完成
```

### 登录失败
```
=========================================
签到结果
=========================================
[3] 登录失败

=========================================
状态码: 3
状态信息: 登录失败
退出码: 1
=========================================

⚠️  签到异常，准备发送通知邮件
```

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
- 日志中账号显示为脱敏格式（如 `2021****23`）
- 代码仓库中不包含任何凭证

⚠️ **注意事项**:
- 不要在公开 Issue/PR 中提及凭证
- 定期更新密码和授权码
- 如果仓库变为公开，重新检查 Secrets 配置

---

## 故障排查

### 签到失败（状态码 3）
**原因**: 账号或密码错误
**解决**:
1. 检查 `SWU_USERNAME` 和 `SWU_PASSWORD` 是否正确
2. 确认账号未被锁定或冻结
3. 尝试在浏览器手动登录验证

### 网络错误（状态码 4）
**原因**: 网络超时或学校系统维护
**解决**:
1. 查看 Actions 日志中的具体错误信息
2. 等待下次自动重试
3. 检查学校系统是否正常

### 今日无签到记录（状态码 0）
**原因**: 学校未发布今日签到任务
**解决**: 属于正常情况，无需处理

### 请假期间（状态码 5）
**原因**: 检测到有效请假记录
**解决**: 属于正常情况，自动跳过签到

### 邮件未收到
1. 检查垃圾邮件文件夹
2. 验证 SMTP 配置是否正确
3. 确认使用授权码而非登录密码
4. 查看 Actions 日志中的邮件发送错误

### Actions 未执行
1. 检查是否已启用自动签到（`ENABLED: true`）
2. 检查仓库是否启用了 Actions
3. 确认工作流文件路径: `.github/workflows/checkin.yml`
4. 验证 cron 表达式格式
5. 检查 Secrets 是否正确配置

---

## 禁用自动签到

### 方法一：关闭开关（推荐）
编辑 `.github/workflows/checkin.yml`，将 `ENABLED: true` 改为 `ENABLED: false`

### 方法二：临时禁用
**Actions** → **自动签到** → **Disable workflow**

### 方法三：永久删除
删除文件: `.github/workflows/checkin.yml`

---

## 高级功能

### 多账号支持
如需为多个账号配置签到：
1. 复制 `checkin.yml` 为 `checkin2.yml`
2. 修改 workflow 名称
3. 使用不同的 Secrets（如 `SWU_USERNAME_2`）
4. 将开关改为 `ENABLED: true`

### 自定义通知内容
编辑 `.github/workflows/checkin.yml` 中的 `body` 部分，自定义邮件模板。

### 添加企业微信/钉钉通知
参考 GitHub Actions 市场中的通知插件，替换邮件发送步骤。
