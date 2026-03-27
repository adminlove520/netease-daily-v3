#!/usr/bin/env python3
"""
网易云音乐 公开 API - 无需登录，获取飙升榜/新歌榜等
兼容 format_daily_songs，输出与日推相同格式
"""
import sys
import requests
from datetime import datetime

# 复用 netease_client 的格式化函数
from netease_client import format_daily_songs, _normalize_song


class NeteasePublicAPI:
    """网易云公开 API 客户端（无需登录）"""

    TOPLISTS = {
        '飙升榜':       19723756,
        '新歌榜':        3779629,
        '热歌榜':        3778678,
        '原创榜':        2884035,
        '说唱榜':      991319590,
        '古典榜':       71385702,
        '黑胶VIP爱听榜': 5453912201,
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Referer': 'https://music.163.com/',
        })

    def get_toplist(self, name: str = '飙升榜') -> dict | None:
        list_id = self.TOPLISTS.get(name)
        if not list_id:
            print(f'❌ 未知榜单: {name}，可用: {", ".join(self.TOPLISTS)}', file=sys.stderr)
            return None

        url = f'https://music.163.com/api/playlist/detail?id={list_id}'
        try:
            resp   = self.session.get(url, timeout=12)
            result = resp.json()
            if result.get('code') == 200:
                playlist = result.get('result', {})
                return {
                    'name':   playlist.get('name', name),
                    'tracks': playlist.get('tracks', [])[:10],
                }
        except Exception as e:
            print(f'❌ 获取榜单失败: {e}', file=sys.stderr)
        return None

    def tracks_to_songs(self, tracks: list) -> list:
        """将公开 API 的 track 格式转换为与日推相同的结构"""
        songs = []
        for t in tracks:
            # 公开 API 字段名与 weapi 略有不同
            artists = t.get('artists') or t.get('ar') or []
            album   = t.get('album')   or t.get('al')   or {}
            songs.append({
                'id':      t.get('id', ''),
                'name':    t.get('name', '未知'),
                'artists': artists,
                'album':   album,
                'dt':      t.get('duration', t.get('dt', 0)),
                'reason':  '',
                'tags':    [],
            })
        return songs


def push_daily(name: str = '飙升榜', output_json: bool = False) -> str:
    """获取榜单并格式化输出（与日推格式统一）"""
    api  = NeteasePublicAPI()
    data = api.get_toplist(name)
    if not data or not data.get('tracks'):
        return '❌ 获取榜单失败'
    songs = api.tracks_to_songs(data['tracks'])
    return format_daily_songs(songs, source=data['name'], output_json=output_json)


if __name__ == '__main__':
    output_json = '--json' in sys.argv
    chart_name  = '飙升榜'
    for arg in sys.argv[1:]:
        if arg in NeteasePublicAPI.TOPLISTS:
            chart_name = arg
            break
        if arg == 'daily':
            break  # 保留向后兼容

    print(push_daily(chart_name, output_json=output_json))
