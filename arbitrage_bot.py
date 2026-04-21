import os
import requests
import json
import time
import pandas as pd
from bs4 import BeautifulSoup

# --- 基本設定 ---
BASE_URL = 'https://www.stockhouse.com.tw'
SENT_IDS_FILE = 'sent_ids.json'

def load_sent_ids():
    if os.path.exists(SENT_IDS_FILE):
        with open(SENT_IDS_FILE, 'r') as f:
            try: return set(json.load(f))
            except: return set()
    return set()

def save_sent_ids(sent_ids):
    with open(SENT_IDS_FILE, 'w') as f:
        json.dump(list(sent_ids), f)

def send_discord_msg(content):
    webhook_url = os.environ.get('DISCORD_WEBHOOK')
    if webhook_url:
        requests.post(webhook_url, json={"content": content})

def get_list(endpoint, type_name):
    payload = {'per_page': '1000', 'page': '1'}
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.post(f"{BASE_URL}/{endpoint}", data=payload, headers=headers)
    res.encoding = 'utf-8'
    # 修正原始 HTML 結構問題
    fixed_html = res.text.replace("<tr id=", "</tr><tr id=")
    soup = BeautifulSoup(fixed_html, 'html.parser')
    rows = soup.find_all('tr', id=True)
    data = []
    for r in rows:
        cols = r.find_all('td')
        if len(cols) >= 4:
            data.append({
                'id': r.get('id'), 
                'name': cols[2].text.strip(), 
                'price': float(cols[3].text.strip() or 0)
            })
    return pd.DataFrame(data)

def get_details(endpoint, item_id):
    """獲取具體的買/賣家清單"""
    payload = {'so_id': item_id, 'child': '1'}
    res = requests.post(f"{BASE_URL}/{endpoint}", data=payload)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    rows = soup.find_all('tr')
    details = []
    for r in rows:
        cols = r.find_all('td')
        if len(cols) >= 3:
            # 格式：名字(數量, 價格)
            details.append(f"{cols[0].text.strip()}({cols[1].text.strip()}個 @ {cols[2].text.strip()})")
    return " | ".join(details[:3]) # 只列出前三名最優的

def main():
    sent_ids = load_sent_ids()
    print("正在抓取清單...")
    
    df_sell = get_list('showallsell2.php', '出售')
    df_buy = get_list('showallbuy2.php', '收購')
    
    if df_sell.empty or df_buy.empty:
        return

    # 透過 ID 合併兩份清單
    merged = pd.merge(df_buy, df_sell, on='id', suffixes=('_buy', '_sell'))
    
    # 核心邏輯：最高收購價 > 最低出售價
    opportunity = merged[merged['price_buy'] > merged['price_sell']]

    if opportunity.empty:
        print("目前沒有發現套利機會。")
        return

    for _, row in opportunity.iterrows():
        item_id = str(row['id'])
        # 如果這個機會沒被通知過，就發送通知
        if item_id not in sent_ids:
            b_detail = get_details('showallbuy2.php', item_id)
            s_detail = get_details('showallsell2.php', item_id)
            
            msg = (f"🔥 **發現套利機會！**\n"
                   f"📦 品項: **{row['name_buy']}**\n"
                   f"💰 收購最高: `{row['price_buy']}` 元\n"
                   f"    買家: {b_detail}\n"
                   f"🏷️ 出售最低: `{row['price_sell']}` 元\n"
                   f"    賣家: {s_detail}\n"
                   f"📈 單件預計利潤: **{row['price_buy'] - row['price_sell']}** 元\n"
                   f"🔗 前往網頁: {BASE_URL}/marketlog.php?z=6&so_id={item_id}")
            
            send_discord_msg(msg)
            sent_ids.add(item_id)
            time.sleep(1)

    save_sent_ids(sent_ids)

if __name__ == "__main__":
    main()
