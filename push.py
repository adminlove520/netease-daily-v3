#!/usr/bin/env python3
"""
网易云音乐 - 推送模块
推送到 GitHub Discussion
"""
import os
import sys
import requests
from pathlib import Path

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv()

# Discussion 配置（支持环境变量覆盖）
REPO_OWNER = os.getenv('REPO_OWNER', 'ythx-101')
REPO_NAME = os.getenv('REPO_NAME', 'openclaw-qa')
# Discussion #133 的 GraphQL global ID
DISCUSSION_ID = os.getenv('DISCUSSION_ID', 'D_kwDORQmU5s4Ak6Wg')

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
    # 优先从 stdin 读取，其次从命令行参数
    content = None
    
    # 检查是否有管道输入
    if not sys.stdin.isatty():
        content = sys.stdin.read().strip()
    elif len(sys.argv) > 1:
        # 从文件读取
        filepath = sys.argv[1]
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
        else:
            content = sys.argv[1]
    
    if content:
        push_to_discussion(content)
    else:
        print("用法: python push.py <content> 或 cat file.txt | python push.py")