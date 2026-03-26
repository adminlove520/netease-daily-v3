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

def main():
    print("=== 🎵 每日一歌 ===\n")
    
    cookie_file = 'secrets/netease_cookies.json'
    has_cookie = os.path.exists(cookie_file)
    content = None
    
    # 先尝试每日推荐
    if has_cookie:
        print("✓ 已登录，尝试获取每日推荐...")
        result = subprocess.run(['python3', 'netease_client.py', 'daily'], 
                                capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and 'ERROR' not in result.stdout and '❌' not in result.stdout:
            content = result.stdout
            print("\n✅ 每日推荐获取成功！")
    
    # 失败或无 Cookie
    if not content:
        if not has_cookie:
            print("⚠️ 未登录")
        else:
            print("⚠️ 每日推荐获取失败")
        
        print("\n尝试获取公开榜单...\n")
        result = subprocess.run(['python3', 'netease_public_api.py', 'daily'],
                               capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            content = result.stdout
            print("\n✅ 公开榜单获取成功")
        else:
            print(f"❌ 获取失败: {result.stderr}")
            return
    
    # 推送（需要 GH_TOKEN 才推送）
    if content and os.environ.get('GH_TOKEN'):
        print("\n📤 推送到 Discussion...")
        subprocess.run(['python3', 'push.py', content])
    elif content:
        print("\n⚠️ 未设置 GH_TOKEN，仅获取内容不推送")

if __name__ == '__main__':
    main()