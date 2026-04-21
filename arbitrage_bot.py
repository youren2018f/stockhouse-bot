import os
import requests

def debug_discord():
    # 1. 檢查變數是否讀取成功
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    
    if not webhook_url:
        print("❌ 錯誤：GitHub Secret 讀取失敗！請檢查 Secret 名稱是否為 DISCORD_WEBHOOK")
        return

    print(f"✅ 成功讀取 Webhook 網址 (前 20 字): {webhook_url[:20]}...")

    payload = {"content": "📢 這是一則診斷訊息"}
    
    try:
        res = requests.post(webhook_url, json=payload)
        # 2. 檢查 HTTP 狀態碼
        if res.status_code == 204:
            print("🚀 Discord 伺服器已成功接收訊息！")
        else:
            print(f"❌ Discord 傳回錯誤代碼：{res.status_code}")
            print(f"錯誤內容：{res.text}")
    except Exception as e:
        print(f"⚠️ 發生網路異常：{e}")

if __name__ == "__main__":
    debug_discord()
