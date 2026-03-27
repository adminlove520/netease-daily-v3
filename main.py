#!/usr/bin/env python3
"""
网易云音乐 · 每日一歌
自动判断：Cookie 有效 → 个性化日推；无效 → 公开榜单
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from netease_client import NeteaseMusicClient, format_daily_songs
from netease_public_api import push_daily as public_daily


def get_daily_content(output_json: bool = False) -> str | None:
    """
    尝试获取内容：
    1. Cookie 存在 → 尝试个性化日推
    2. 日推失败或无 Cookie → 公开榜单
    返回格式化后的字符串，失败返回 None。
    """
    cookie_file = 'secrets/netease_cookies.json'
    client      = NeteaseMusicClient(cookies_file=cookie_file)
    content     = None

    if os.path.exists(cookie_file):
        print('✓ 检测到 Cookie，尝试获取个性化日推...', flush=True)
        if client.load_cookies():
            songs = client.get_daily_recommend()
            if songs:
                # 补充歌曲详情（标签/别名/时长）
                song_ids     = [s.get('id') for s in songs[:10] if s.get('id')]
                song_details = client.get_song_detail(song_ids)
                details_map  = {s.get('id'): s for s in song_details}
                for song in songs:
                    detail = details_map.get(song.get('id'), {})
                    if detail.get('tags') and not song.get('tags'):
                        song['tags'] = detail['tags']
                    elif not song.get('tags'):
                        song['tags'] = detail.get('alia', [])[:2]
                    if not song.get('dt') and detail.get('dt'):
                        song['dt'] = detail['dt']

                content = format_daily_songs(songs, source='日推', output_json=output_json)
                print('✅ 个性化日推获取成功！', flush=True)
            else:
                print('⚠️  日推接口返回空，Cookie 可能已过期', flush=True)
        else:
            print('⚠️  Cookie 格式异常', flush=True)
    else:
        print('⚠️  未检测到 Cookie，跳过日推', flush=True)

    if not content:
        print('\n↩  切换到公开榜单（飙升榜）...', flush=True)
        content = public_daily('飙升榜', output_json=output_json)
        if content and '❌' not in content:
            print('✅ 公开榜单获取成功', flush=True)
        else:
            print('❌ 公开榜单获取失败', file=sys.stderr)
            return None

    return content


def push_content(content: str) -> bool:
    """将内容推送到 GitHub Discussion"""
    from push import push_to_discussion
    return push_to_discussion(content)


def main() -> None:
    output_json = '--json' in sys.argv
    print('=== 🎵 每日一歌 ===\n', flush=True)

    content = get_daily_content(output_json=output_json)
    if not content:
        print('❌ 无法获取任何内容，退出', file=sys.stderr)
        sys.exit(1)

    gh_token = os.environ.get('GH_TOKEN')
    if gh_token:
        print('\n📤 推送到 GitHub Discussion...', flush=True)
        push_content(content)
    else:
        print('\n⚠️  未设置 GH_TOKEN，仅打印内容（不推送）\n', flush=True)
        print('=' * 60)
        print(content)


if __name__ == '__main__':
    main()
