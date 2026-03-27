#!/usr/bin/env python3
"""
网易云音乐API - 支持登录获取个性化日推
实现了网易云weapi的加密逻辑
"""
import requests
import json
import base64
import os
import sys
from datetime import datetime
from urllib.parse import quote
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# lyric-sense 网页地址（可通过环境变量覆盖）
LYRIC_SENSE_URL = os.getenv(
    'LYRIC_SENSE_URL',
    'https://adminlove520.github.io/lyric-sense'
)


class NeteaseCrypto:
    """网易云加密工具"""

    MODULUS = ('00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725'
               '152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312'
               'ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b42'
               '4d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7')
    NONCE  = '0CoJUm6Qyw8W8jud'
    PUBKEY = '010001'
    IV     = '0102030405060708'

    @staticmethod
    def aes_encrypt(text: str, key: str) -> str:
        """AES-CBC 加密（PKCS7 填充）"""
        pad_len = 16 - len(text) % 16
        text += chr(pad_len) * pad_len
        cipher = Cipher(
            algorithms.AES(key.encode('utf-8')),
            modes.CBC(NeteaseCrypto.IV.encode('utf-8')),
            backend=default_backend()
        )
        enc = cipher.encryptor()
        return base64.b64encode(enc.update(text.encode('utf-8')) + enc.finalize()).decode('utf-8')

    @staticmethod
    def rsa_encrypt(text: str, pubkey: str, modulus: str) -> str:
        """RSA 加密"""
        text_int = int.from_bytes(text[::-1].encode('utf-8'), 'big')
        result   = pow(text_int, int(pubkey, 16), int(modulus, 16))
        return format(result, 'x').zfill(256)

    @staticmethod
    def encrypt(params: dict) -> dict:
        """网易云 weapi 加密"""
        sec_key  = ''.join(chr(ord('a') + (b % 26)) for b in os.urandom(16))
        enc_text = NeteaseCrypto.aes_encrypt(json.dumps(params), NeteaseCrypto.NONCE)
        enc_text = NeteaseCrypto.aes_encrypt(enc_text, sec_key)
        enc_key  = NeteaseCrypto.rsa_encrypt(sec_key, NeteaseCrypto.PUBKEY, NeteaseCrypto.MODULUS)
        return {'params': enc_text, 'encSecKey': enc_key}


class NeteaseMusicClient:
    """网易云音乐客户端"""

    DEFAULT_HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
        'Referer':      'https://music.163.com/',
        'Origin':       'https://music.163.com',
        'Accept':       '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    def __init__(self, cookies_file: str = 'secrets/netease_cookies.json'):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self.crypto = NeteaseCrypto()
        self.cookies_file = cookies_file

    # ── 底层请求 ──────────────────────────────────────
    def weapi_request(self, endpoint: str, params: dict = None) -> dict:
        url    = f'https://music.163.com/weapi{endpoint}'
        params = params or {}
        params['csrf_token'] = self.session.cookies.get('__csrf', '')
        try:
            resp = self.session.post(url, data=self.crypto.encrypt(params), timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f'❌ 请求失败: {e}', file=sys.stderr)
            return {'code': -1, 'msg': str(e)}

    # ── 认证 ──────────────────────────────────────────
    def send_captcha(self, phone: str) -> bool:
        result = self.weapi_request('/sms/captcha/sent', {
            'cellphone': phone, 'ctcode': '86'
        })
        if result.get('code') == 200:
            print(f'✅ 验证码已发送到 {phone}（5 分钟内有效）')
            return True
        print(f'❌ 发送失败: {result.get("message", result.get("msg", "未知错误"))}')
        return False

    def login_with_captcha(self, phone: str, captcha: str) -> bool:
        result = self.weapi_request('/login/cellphone', {
            'phone': phone, 'captcha': captcha,
            'countrycode': '86', 'rememberLogin': 'true'
        })
        if result.get('code') == 200:
            nickname = result.get('profile', {}).get('nickname', '用户')
            print(f'✅ 登录成功！欢迎回来，{nickname}～')
            self.save_cookies()
            return True
        print(f'❌ 登录失败: {result.get("message", result.get("msg", "未知错误"))}')
        return False

    # ── 数据接口 ──────────────────────────────────────
    def get_daily_recommend(self) -> list:
        """获取个性化日推歌曲（需要登录）"""
        result = self.weapi_request('/v1/discovery/recommend/songs', {
            'offset': 0, 'total': True, 'limit': 20
        })
        if result.get('code') == 200:
            return result.get('data', {}).get('dailySongs', [])
        return []

    def get_song_detail(self, song_ids: list) -> list:
        """获取歌曲详情（含别名/风格标签）"""
        ids_str = ','.join(str(i) for i in song_ids)
        result  = self.weapi_request('/v3/song/detail', {
            'c':   json.dumps([{'id': int(i)} for i in song_ids]),
            'ids': ids_str,
        })
        return result.get('songs', []) if result.get('code') == 200 else []

    # ── Cookie 管理 ───────────────────────────────────
    def save_cookies(self) -> None:
        os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
        seen, cookies_dict = set(), {}
        for c in self.session.cookies:
            if c.name not in seen:
                cookies_dict[c.name] = c.value
                seen.add(c.name)
        with open(self.cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies_dict, f, ensure_ascii=False, indent=2)
        print('💾 登录状态已保存')

    def load_cookies(self) -> bool:
        try:
            with open(self.cookies_file, 'r', encoding='utf-8') as f:
                self.session.cookies.update(json.load(f))
            return True
        except (FileNotFoundError, json.JSONDecodeError):
            return False


# ── 工具函数 ─────────────────────────────────────────

def _lyric_sense_link(artist: str, name: str) -> str:
    """生成 lyric-sense 歌词界面链接"""
    return (f'{LYRIC_SENSE_URL}/'
            f'?artist={quote(artist)}&title={quote(name)}')


def _lrc_api_link(artist: str, name: str) -> str:
    """生成 LrcApi 直接查询链接"""
    return (f'https://api.lrc.cx/lyrics'
            f'?artist={quote(artist)}&title={quote(name)}')


def _duration_str(ms: int) -> str:
    """毫秒转 mm:ss"""
    sec = ms // 1000
    return f'{sec // 60}:{sec % 60:02d}'


def _normalize_song(song: dict) -> dict:
    """将原始 song 对象规范化为统一结构"""
    song_id = song.get('id', '')
    name    = song.get('name', '未知')
    artists = song.get('artists', song.get('ar', []))
    artist  = ' / '.join(a.get('name', '') for a in artists[:2] if a.get('name'))
    album   = (song.get('album') or song.get('al') or {}).get('name', '')
    dur_ms  = song.get('dt', song.get('duration', 0))
    tags    = song.get('tags') or []
    reason  = song.get('reason', '')

    nc_url      = f'https://music.163.com/song?id={song_id}' if song_id else ''
    lyric_page  = _lyric_sense_link(artist, name) if artist else ''
    lrc_api     = _lrc_api_link(artist, name)     if artist else ''

    return {
        'id':         song_id,
        'name':       name,
        'artist':     artist,
        'album':      album,
        'duration':   _duration_str(dur_ms) if dur_ms else '',
        'url':        nc_url,
        'lyric_url':  lyric_page,
        'lrc_api':    lrc_api,
        'tags':       tags,
        'reason':     reason,
    }


def format_daily_songs(songs: list, date_str: str = None,
                       source: str = '日推', output_json: bool = False) -> str:
    """
    格式化歌曲列表。

    Args:
        songs:       原始歌曲列表（来自 weapi 或公开 API）
        date_str:    显示日期字符串，默认今日
        source:      来源标签，如「日推」「飙升榜」
        output_json: 若 True，返回 JSON 格式（供龙虾进一步调用）

    Returns:
        Markdown 格式字符串（GitHub Discussion 友好）或 JSON 字符串
    """
    if not songs:
        return '❌ 暂无推荐歌曲'

    date      = date_str or datetime.now().strftime('%m月%d日')
    year      = datetime.now().strftime('%Y')
    norm_list = [_normalize_song(s) for s in songs[:10]]

    # ── JSON 输出 ──────────────────────────────────────
    if output_json:
        payload = {
            'date':   datetime.now().strftime('%Y-%m-%d'),
            'type':   source,
            'source': 'netease-daily-v3',
            'songs':  norm_list,
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    # ── Markdown 输出 ─────────────────────────────────
    header = (
        f'## 🎵 网易云 · {source} · {date}\n\n'
        f'> 📅 {year}年{date} · 共 {len(norm_list)} 首'
        + (f'  \n> 🎧 [打开网易云](https://music.163.com/)' if True else '')
        + '\n\n'
    )

    # 歌曲表格
    table_rows = ['| # | 歌曲 | 歌手 | 专辑 | 时长 | 歌词 |',
                  '|---|------|------|------|------|------|']

    for i, s in enumerate(norm_list, 1):
        name_cell   = f'[{s["name"]}]({s["url"]})' if s['url'] else s['name']
        lyric_cell  = f'[🎵 歌词]({s["lyric_url"]})' if s['lyric_url'] else '—'
        album_cell  = s['album'] or '—'
        dur_cell    = s['duration'] or '—'
        table_rows.append(
            f'| {i} | {name_cell} | {s["artist"] or "—"} | {album_cell} | {dur_cell} | {lyric_cell} |'
        )

    # 带推荐理由的附加信息（折叠展示）
    detail_lines = []
    for i, s in enumerate(norm_list, 1):
        extras = []
        if s['tags']:
            extras.append(f'🏷️ {" · ".join(s["tags"][:3])}')
        if s['reason']:
            extras.append(f'💡 {s["reason"]}')
        if extras:
            detail_lines.append(f'**{i}. {s["name"]}** — ' + '  '.join(extras))

    details_block = ''
    if detail_lines:
        details_block = ('\n<details>\n<summary>📖 推荐理由 & 风格标签</summary>\n\n'
                         + '\n'.join(detail_lines)
                         + '\n\n</details>\n')

    footer = (
        '\n---\n'
        '🦞 由 [netease-daily-v3](https://github.com/adminlove520/netease-daily-v3) 自动推送  '
        '· 歌词由 [lyric-sense](https://github.com/adminlove520/lyric-sense) 提供  \n'
        '🌟 每日 09:00 更新'
    )

    return header + '\n'.join(table_rows) + '\n' + details_block + footer


def main():
    client = NeteaseMusicClient()

    if len(sys.argv) < 2:
        print('用法:')
        print('  python3 netease_client.py send_captcha <手机号>')
        print('  python3 netease_client.py login <手机号> <验证码>')
        print('  python3 netease_client.py daily [--json]')
        return

    cmd  = sys.argv[1]
    args = sys.argv[2:]

    if cmd == 'send_captcha' and args:
        client.send_captcha(args[0])

    elif cmd == 'login' and len(args) >= 2:
        client.login_with_captcha(args[0], args[1])

    elif cmd == 'daily':
        output_json = '--json' in args
        if not client.load_cookies():
            print('❌ 未登录，请先使用 login 命令登录', file=sys.stderr)
            sys.exit(1)

        songs = client.get_daily_recommend()
        if not songs:
            print('❌ 获取日推失败，请检查登录状态', file=sys.stderr)
            sys.exit(1)

        # 获取歌曲详情（含标签）
        song_ids     = [s.get('id') for s in songs[:10] if s.get('id')]
        song_details = client.get_song_detail(song_ids)
        details_map  = {s.get('id'): s for s in song_details}

        for song in songs:
            detail = details_map.get(song.get('id'), {})
            if detail.get('tags'):
                song['tags'] = detail['tags']
            elif not song.get('tags'):
                song['tags'] = detail.get('alia', [])[:2]
            # 补充时长
            if not song.get('dt') and detail.get('dt'):
                song['dt'] = detail['dt']

        print(format_daily_songs(songs, output_json=output_json))

    else:
        print(f'未知命令: {cmd}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
