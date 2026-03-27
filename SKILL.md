---
name: netease-daily-v3
version: 2.0.0
description: >
  自动获取网易云音乐每日推荐歌单并推送到 GitHub Discussion 的 OpenClaw 技能。
  登录后获取个性化日推；未登录时退回公开榜单。
  支持与 lyric-sense 联动，为每首歌自动附上歌词跳转链接。
author: 小溪
homepage: https://github.com/adminlove520/netease-daily-v3
license: MIT
triggers:
  - 今天推荐
  - 每日推荐
  - 网易云日推
  - 日推歌单
  - 今日歌单
  - 网易云歌单
  - 每天的歌
  - daily recommend
  - 帮我看看今天推荐什么歌
always_apply: false
---

# netease-daily-v3 日推技能

自动获取网易云音乐每日推荐，推送到 GitHub Discussion，并与 lyric-sense 联动。

## 功能

1. **个性化日推** — 登录后获取专属日推（需配置 Cookie）
2. **公开榜单兜底** — 未登录或 Cookie 失效时自动切换公开榜单
3. **自动推送** — 通过 GitHub Actions 每日定时推送到 Discussion
4. **歌词联动** — 每首歌自动附上 lyric-sense 歌词界面跳转链接
5. **结构化输出** — 同时输出 Markdown 和 JSON 两种格式，方便龙虾进一步处理

## 工作流程

```
每日 UTC 01:00 (北京时间 09:00)
  ↓
检查 secrets/netease_cookies.json
  ↓ 有效               ↓ 无效/不存在
获取个性化日推        获取公开飙升榜
  ↓
格式化输出（Markdown + JSON）
  ↓
附上 lyric-sense 歌词链接
  ↓
推送到 GitHub Discussion
```

## 输出格式

### Markdown 格式（GitHub Discussion 展示）

```markdown
🎵 网易云日推 · 03月27日
📅 专属于你的每日推荐 · 10首

| # | 歌曲 | 歌手 | 专辑 | 歌词 |
|---|------|------|------|------|
| 1 | [晚安](https://music.163.com/song?id=xxx) | 颜人中 | 晚安 | [🎵 查看歌词](https://adminlove520.github.io/lyric-sense/?artist=颜人中&title=晚安) |
...

🎧 打开网易云收听完整版
```

### JSON 格式（供龙虾进一步处理）

```json
{
  "date": "2026-03-27",
  "type": "daily",
  "songs": [
    {
      "id": 123456,
      "name": "晚安",
      "artist": "颜人中",
      "album": "晚安",
      "duration": 234,
      "url": "https://music.163.com/song?id=123456",
      "lyric_url": "https://adminlove520.github.io/lyric-sense/?artist=颜人中&title=晚安",
      "lrc_api": "https://api.lrc.cx/lyrics?artist=颜人中&title=晚安"
    }
  ]
}
```

## 龙虾使用示例

### 示例 1：获取今日日推

**用户：** 帮我看看今天网易云推荐什么歌

**龙虾：** 读取最新 Discussion 内容或直接运行脚本获取：

```bash
python3 main.py
```

### 示例 2：联动 lyric-sense 查看歌词

**用户：** 帮我看看今天日推第一首歌的歌词

龙虾从日推 JSON 输出中取出第一首，调用 lyric-sense：

```javascript
const song = dailySongs[0];
const lrcResp = await fetch('https://corsproxy.io/?' + encodeURIComponent(song.lrc_api));
const lrc = await lrcResp.text();
// 解析并展示歌词...
```

### 示例 3：触发手动推送

```bash
# 手动运行
python3 main.py

# 通过 GitHub Actions 手动触发
# Actions → 每日一歌 → Run workflow
```

## 配置

### GitHub Secrets

| Secret | 必需 | 说明 |
|--------|------|------|
| `GH_TOKEN` | ✅ | GitHub Token（需要 `write:discussion` 权限） |
| `NCM_COOKIE` | ❌ | 登录 Cookie（有则获取日推，无则使用榜单） |

### 环境变量（.env）

```env
# 推送目标（GitHub Discussion）
REPO_OWNER=ythx-101
REPO_NAME=openclaw-qa
DISCUSSION_ID=D_kwDORQmU5s4Ak6Wg

# lyric-sense 界面地址（默认使用 GitHub Pages）
LYRIC_SENSE_URL=https://adminlove520.github.io/lyric-sense
```

### 获取 Cookie（首次登录）

```bash
# 1. 发送验证码
python3 netease_client.py send_captcha 13800138000

# 2. 输入验证码登录
python3 netease_client.py login 13800138000 123456

# 3. Cookie 自动保存到 secrets/netease_cookies.json
# 4. 将文件内容设置为 GitHub Secret NCM_COOKIE
```

## 项目结构

```
netease-daily-v3/
├── main.py                 # 主程序（自动判断日推/榜单）
├── netease_client.py       # 登录 + 个性化日推（含 weapi 加密）
├── netease_public_api.py   # 公开榜单（无需登录）
├── push.py                 # GitHub Discussion 推送模块
├── .github/
│   └── workflows/
│       └── daily.yml       # GitHub Actions 定时任务
├── secrets/                # Cookie 存储（不提交 git）
├── .env.example            # 环境变量模板
└── SKILL.md                # 本文件
```

## 与 lyric-sense 联动

两个技能天然互补：

- **netease-daily-v3** 负责发现每日好歌（数据源）
- **lyric-sense** 负责展示歌词（内容消费）

联动效果：日推列表中每首歌带有「查看歌词」链接，点击直达 lyric-sense 同步界面。

相关项目：[lyric-sense](https://github.com/adminlove520/lyric-sense)

## 注意事项

- Cookie 有效期约 1 个月，过期后自动切换公开榜单
- GitHub Discussion 推送需要 `write:discussion` 权限的 Token
- 公开榜单无需任何登录，始终可用
- 本地运行不设置 `GH_TOKEN` 时仅打印内容，不推送

---

🦞 Skill for OpenClaw | Made by 小溪 | v2.0.0
