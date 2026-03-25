# Changelog

## [1.0.0] - 2026-03-25

### Added
- 自动获取网易云音乐每日推荐
- 验证码登录支持
- 公开榜单支持（飙升榜、新歌榜等）
- 自动推送到 GitHub Discussion
- 解耦的推送模块（方便扩展）

### Scripts
- `main.py` - 主程序
- `push.py` - 推送模块
- `netease_client.py` - 登录 + 每日推荐
- `netease_public_api.py` - 公开榜单

### Features
- 自动判断登录状态
- Cookie 有效 → 推送日推
- Cookie 无效 → 推送榜单
- 推送到 openclaw-qa/tech-table Discussion #133