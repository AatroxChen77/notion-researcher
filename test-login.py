from notion_client import Client

# 把你的 ntn_ Token 填进去
token = "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" 

try:
    client = Client(auth=token)
    # 试着列出 workspace 里所有的用户（这是最基本的权限）
    users = client.users.list()
    print("✅ 登录成功！Token 是有效的。")
except Exception as e:
    print(f"❌ 登录失败: {e}")