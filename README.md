# 每日一歌 🎵

> 每天自动获取网易云音乐推荐，推送到 GitHub Discussion

## 脚本说明

| 脚本 | 功能 | 需要登录 |
|------|------|----------|
| `main.py` | 主程序（自动判断 + 推送） | 可选 |
| `push.py` | 推送模块 | ✅ GH_TOKEN |
| `netease_client.py` | 验证码登录 + 每日推荐 | ✅ |
| `netease_public_api.py` | 公开榜单 | ❌ |

## 本地开发

### 1. 安装依赖
```bash
pip3 install cryptography requests python-dotenv
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写：
```bash
cp .env.example .env
# 编辑 .env 填入你的 GH_TOKEN
```

`.env` 内容：
```bash
GH_TOKEN=your_github_token_here
# 可选配置
# REPO_OWNER=ythx-101
# REPO_NAME=openclaw-qa
# DISCUSSION_ID=133
```

### 3. 登录（可选）
```bash
python3 netease_client.py send_captcha <手机号>
python3 netease_client.py login <手机号> <验证码>
```

### 4. 运行
```bash
python3 main.py
```

## 自动逻辑

```
main.py
├── 有 Cookie → netease_client.py daily → 成功 → 推送日推
│               └── 失败 → netease_public_api.py → 推送榜单
└── 无 Cookie → netease_public_api.py → 推送榜单
```

**注意**：没有设置 `GH_TOKEN` 时，程序只会获取内容但不会推送

## GitHub Workflow

### 定时推送

- 每天 UTC 9点 = 北京时间 17点
- 也可以手动触发 (workflow_dispatch)

### 配置 Secrets

| Secret | 说明 |
|--------|------|
| `GH_TOKEN` | GitHub Token（需要 discussion 权限） |
| `NCM_COOKIE` | 登录后的 Cookie（可选） |

### 推送目标

- 仓库: ythx-101/openclaw-qa
- Discussion: #133 (茶馆)

## 目录结构

```
netease-v3/
├── main.py                   # 主程序
├── push.py                   # 推送模块
├── netease_client.py         # 登录+日推
├── netease_public_api.py     # 榜单
├── .env.example              # 环境变量模板
├── .gitignore                # Git 忽略
├── .github/workflows/daily.yml
└── secrets/                  # Cookie 存储（不提交）
```

## 许可证

MIT