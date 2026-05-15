import requests
import os

# 讀取 GitHub 幫你藏好的 Webhook 網址
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

def send_test_message():
    if not WEBHOOK_URL:
        print("錯誤：找不到 Webhook 網址，請檢查 Settings 裡的 Secrets 設定！")
        return

    # 這裡先寫死一個測試用的白色 Embed，晚點拿到 Riot 授權再換成真的商店
    payload = {
        "content": "✨ **Valorant 每日商店機器人測試**",
        "embeds": [
            {
                "title": "離子初始 狂暴 (測試商品)",
                "description": "如果看到這個訊息，代表你的自動排程跟 Webhook 連線成功了！",
                "color": 16777215, # 純白色
                "image": {
                    "url": "https://media.valorant-api.com/v1/weapons/skinlevels/93437148-433b-cdb1-2131-41be3f6b4be9/displayIcon.png"
                },
                "footer": {
                    "text": "Zenith Shop Bot 運作中"
                }
            }
        ]
    }
    
    res = requests.post(WEBHOOK_URL, json=payload)
    if res.status_code == 204:
        print("Discord 訊息發送成功！")
    else:
        print(f"發送失敗，錯誤代碼：{res.status_code}")

if __name__ == "__main__":
    send_test_message()
