import os
import requests
import json

def send_discord_msg(content):
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if not webhook_url: return
    requests.post(webhook_url, json={"content": content})

if __name__ == "__main__":
    send_discord_msg("✅ 專案建立與連線測試成功！")
