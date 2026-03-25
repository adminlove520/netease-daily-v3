#!/usr/bin/env python3
"""
网易云音乐 - 主程序
自动判断：Cookie 有效→日推，无效→榜单，推送到 Discussion
"""
import os
import sys
import subprocess
import requests
import json

# Discussion 配置
REPO_OWNER = "openclaw-qa"
REPO_NAME = "tech-table"
DISCUSSION_ID = 133  # 茶馆 Discussion #133

def post_to_discussion(content):
    """推送到 GitHub Discussion"""
    token = os.environ.get('GH_TOKEN')
    if not token:
        print("❌ 未设置 GH_TOKEN")
        return False
    
    query = """
    mutation($discussionId: ID!, $body: String!) {
        addDiscussionComment(input: {discussionId: $discussionId, body: $body}) {
            comment { id }
        }
    }
    """
    
    variables = {
        "discussionId": str(DISCUSSION_ID),
        "body": content
    }
    
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json={"query": query, "variables": variables}, 
                                headers=headers, timeout=15)
        result = response.json()
        
        if 'data' in result and result['data'].get('addDiscussionComment'):
            print("✅ 推送成功！")
            return True
        else:
            print(f"❌ 推送失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 推送异常: {e}")
        return False

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
    
    # 推送到 Discussion
    if content:
        print("\n📤 推送到茶馆...")
        post_to_discussion(content)

if __name__ == '__main__':
    main()