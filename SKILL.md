# netease-daily-song

自动获取网易云音乐每日推荐，推送到 GitHub Discussion

## 功能

- 🎵 获取每日推荐歌曲（需要登录）
- 📊 获取公开榜单（无需登录）
- 📢 自动推送到 GitHub Discussion
- 🔄 自动判断登录状态

## 使用方式

### 登录（获取 Cookie）

```bash
# 发送验证码
python3 netease_client.py send_captcha <手机号>

# 验证码登录
python3 netease_client.py login <手机号> <验证码>
```

### 运行

```bash
# 主程序（自动判断）
python3 main.py

# 单独获取每日推荐
python3 netease_client.py daily

# 单独获取榜单
python3 netease_public_api.py daily
```

## 项目结构

```
netease-daily/
├── main.py                 # 主程序
├── push.py                 # 推送模块
├── netease_client.py       # 登录 + 每日推荐
├── netease_public_api.py   # 公开榜单
├── .github/workflows/      # GitHub Actions
└── secrets/               # Cookie 存储
```

## 配置

### GitHub Secrets

| Secret | 说明 |
|--------|------|
| `GH_TOKEN` | GitHub Token |
| `NCM_COOKIE` | 登录后的 Cookie |

## License

MIT