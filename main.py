import requests
import os

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

def get_skin_data(uuid):
    try:
        res = requests.get(f"https://valorant-api.com/v1/weapons/skinlevels/{uuid}?language=zh-TW")
        if res.status_code == 200:
            data = res.json()["data"]
            return data["displayName"], data["displayIcon"]
    except:
        pass
    return "未知造型", "https://media.valorant-api.com/v1/playercards/9fb348bc-41a4-91ad-d131-159c865c364f/displayIcon.png"

def send_shop_webhook():
    if not WEBHOOK_URL:
        print("錯誤：找不到 WEBHOOK_URL")
        return

    # 預設四個熱門造型 UUID (離子狂暴、蓋亞暴徒、至尊警長、奇幻鬼魅)
    test_shop_uuids = [
        "93437148-433b-cdb1-2131-41be3f6b4be9",
        "dbcd4db4-406c-c2f8-9571-08bad044eb75",
        "f4b43445-4299-cd80-32ff-1fa23e597bf6",
        "e6e66e74-4b53-4813-90d5-fb95ef9295db"
    ]

    embeds = [
        {
            "description": "每日商店供 **玩家#TW1** 使用（新商店 in 1 day）",
            "color": 16777215  # 純白色邊條
        }
    ]

    for uuid in test_shop_uuids:
        name, icon_url = get_skin_data(uuid)
        embeds.append({
            "title": name,
            "description": "💰 特務幣商店商品",
            "color": 2829619,  # 深色背景
            "thumbnail": {
                "url": icon_url
            }
        })

    payload = {
        "username": "終究還是刷不到嗎?",
        "avatar_url": "https://media.valorant-api.com/v1/playercards/9fb348bc-41a4-91ad-d131-159c865c364f/displayIcon.png",
        "embeds": embeds
    }

    res = requests.post(WEBHOOK_URL, json=payload)
    if res.status_code == 204:
        print("成功發送！")
    else:
        print(f"失敗：{res.status_code}")

if __name__ == "__main__":
    send_shop_webhook()
