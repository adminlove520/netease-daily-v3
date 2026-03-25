#!/usr/bin/env python3
"""
网易云音乐 - 推送模块
推送到 GitHub Discussion
"""
import os
import requests

# Discussion 配置
REPO_OWNER = "ythx-101"
REPO_NAME = "openclaw-qa"
DISCUSSION_ID = 133

def push_to_discussion(content):
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

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        content = sys.argv[1]
        push_to_discussion(content)
    else:
        print("用法: python3 push.py <content>")