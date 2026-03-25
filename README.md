# 每日一歌 🎵

> 每天自动获取网易云音乐推荐，基于 netease-music-pusher

## 脚本说明

| 脚本 | 功能 | 需要登录 |
|------|------|----------|
| `main.py` | 主程序（自动判断） | 可选 |
| `netease_client.py` | 验证码登录 + 每日推荐 | ✅ |
| `netease_public_api.py` | 公开榜单 | ❌ |

## 使用方式

### 1. 安装依赖
```bash
pip3 install cryptography requests
```

### 2. 登录（可选）
```bash
python3 netease_client.py send_captcha <手机号>
python3 netease_client.py login <手机号> <验证码>
```

### 3. 运行
```bash
python3 main.py
```

## 主程序逻辑

```
main.py
├── 有 Cookie → netease_client.py daily → 成功 → 推送日推
│               └── 失败 → netease_public_api.py toplist → 推送榜单
└── 无 Cookie → netease_public_api.py toplist → 推送榜单
```

## GitHub Workflow

配置 Secrets：
- `GH_TOKEN`
- `NCM_COOKIE`

## 目录结构

```
netease-v3/
├── main.py                   # 主程序
├── netease_client.py         # 来自 netease-music-pusher
├── netease_public_api.py     # 来自 netease-music-pusher
├── .github/workflows/        # 定时任务
└── secrets/                 # Cookie 存储
```

## 许可证

MIT