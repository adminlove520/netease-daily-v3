#!/usr/bin/env python3
"""
网易云音乐 - 主程序
自动判断：Cookie 有效→日推，无效→榜单
"""
import os
import sys
import subprocess

# 加载 .env 文件（本地开发时使用）
from dotenv import load_dotenv
load_dotenv()

# 获取 Python 解释器（兼容 Windows）
PYTHON = sys.executable if sys.platform == 'win32' else 'python3'

def main():
    print("=== 🎵 每日一歌 ===\n")
    
    cookie_file = 'secrets/netease_cookies.json'
    has_cookie = os.path.exists(cookie_file)
    content = None
    
    # 先尝试每日推荐
    if has_cookie:
        print("✓ 已登录，尝试获取每日推荐...")
        result = subprocess.run([PYTHON, 'netease_client.py', 'daily'], 
                                capture_output=True, text=True, timeout=30)
        
        # 检查是否成功（不包含错误关键字）
        if result.returncode == 0 and 'ERROR' not in result.stdout and '❌' not in result.stdout:
            content = result.stdout
            print("\n✅ 每日推荐获取成功！")
        else:
            print(f"⚠️ 日推失败: {result.stderr or result.stdout[:200]}")
    
    # 失败或无 Cookie
    if not content:
        if not has_cookie:
            print("⚠️ 未登录")
        else:
            print("⚠️ 每日推荐获取失败")
        
        print("\n尝试获取公开榜单...\n")
        result = subprocess.run([PYTHON, 'netease_public_api.py', 'daily'],
                               capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout:
            content = result.stdout
            print("\n✅ 公开榜单获取成功")
        else:
            print(f"❌ 获取榜单失败: {result.stderr or result.stdout[:200]}")
            return
    
    # 推送（需要 GH_TOKEN 才推送）
    if content and os.environ.get('GH_TOKEN'):
        print("\n📤 推送到 Discussion...")
        # Windows 需要用 shell=True 或通过文件传递
        if sys.platform == 'win32':
            # 写入临时文件
            with open('temp_content.txt', 'w', encoding='utf-8') as f:
                f.write(content)
            subprocess.run([PYTHON, 'push.py', 'temp_content.txt'])
            os.remove('temp_content.txt')
        else:
            subprocess.run([PYTHON, 'push.py'], input=content, text=True)
    elif content:
        print("\n⚠️ 未设置 GH_TOKEN，仅获取内容不推送")
        print("\n" + "="*40)
        print(content)

if __name__ == '__main__':
    main()