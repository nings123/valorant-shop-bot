import discord
from discord import app_commands
import requests
import os
import re
import base64
import json

# 從環境變數讀取 Bot Token
BOT_TOKEN = os.environ.get("BOT_TOKEN")

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"🤖 機器人 {bot.user} 已上線，超完美教學型商店查詢就緒！")

# 獲取武器皮膚資料的輔助函式
def get_skin_data(uuid):
    try:
        res = requests.get("https://valorant-api.com/v1/weapons/skins?language=zh-TW")
        if res.status_code == 200:
            skins = res.json()["data"]
            for skin in skins:
                for chroma in skin["chromas"]:
                    if chroma["uuid"] == uuid:
                        return skin["displayName"], chroma["displayIcon"]
                for level in skin["levels"]:
                    if level["uuid"] == uuid:
                        return skin["displayName"], level["displayIcon"]
    except Exception as e:
        print(f"⚠️ API解析錯誤: {e}")
    return "未知造型", "https://media.valorant-api.com/v1/playercards/9fb348bc-41a4-91ad-d131-159c865c364f/displayIcon.png"

# Discord 斜線指令：/shop (把兩格都改成 = None，變成選填)
@bot.tree.command(name="shop", description="查詢你的每日特戰商店 (留空發送可看獲取教學)")
@app_commands.describe(
    access_token="直接貼上獲取到的『整條完整長網址』，第一次使用請直接留空送出看教學", 
    user_id="此欄位『完全不用填』，留空即可！"
)
async def shop(interaction: discord.Interaction, access_token: str = None, user_id: str = None):
    
    # 【自動解析機制】如果群友有填網址，後端自動切開
    if access_token and ("access_token=" in access_token or "login.live.com" in access_token):
        url_input = access_token
        access_match = re.search(r'access_token=([^&]+)', url_input)
        id_token_match = re.search(r'id_token=([^&]+)', url_input)
        
        if access_match:
            access_token = access_match.group(1)
            if id_token_match:
                try:
                    payload_b64 = id_token_match.group(1).split('.')[1]
                    payload_b64 += '=' * (-len(payload_b64) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
                    user_id = payload.get('sub')
                except:
                    pass

    # 🔥 重點：如果群友什麼都沒填（第一次用），或者網址填錯，直接噴出超精美教學
    if not access_token or not user_id:
        embed = discord.Embed(
            title="✨特戰每日商店查詢教學",
            description=(
                "為了保障您的帳號安全，本機器人**絕對不會收集或索取您的帳號密碼**。 🛡️\n"
                "請在電腦上依照下方簡單的三個步驟，獲取官方的安全授權碼：\n\n"
                "1️⃣ **第一步：登入 Riot 官網**\n"
                "請先點擊下方連結完成登入（確認看到自己的 Riot ID 即可）：\n"
                "[👉 點我前往 Riot 官方登入中心](https://account.riotgames.com/)\n\n"
                "2️⃣ **第二步：一鍵獲取安全授權碼**\n"
                "登入成功後**請勿關閉網頁**，直接在同一個瀏覽器點擊下方安全通道按鈕。\n"
                "*(💡 註：點過去後畫面會彈出微軟的空白網頁，這完全是正常的！)*\n"
                "[🔗 點我一鍵獲取安全 Token 網址](https://auth.riotgames.com/authorize?client_id=play-valorant-web-prod&response_type=token+id_token&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf&scope=openid+link+ban&nonce=1)\n\n"
                "3️⃣ **第三步：整條複製並貼回查詢**\n"
                "請把那個微軟空白網頁最上方網址列的**「那一整條超長網址」全部複製起來**！\n\n"
                "再次回到 Discord 輸入 `/shop`，直接把那條長網址貼在 `access_token` 框框裡（第二格留空），按下 Enter 就能秒出你的商店造型卡片啦！"
            ),
            color=0xFFFFFF
        )
        # 用 ephemeral=True 讓教學只有輸入指令的群友自己看得到，不洗頻
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # 進入查詢流程（只有兩格都有正確解析到才會走到這裡）
    await interaction.response.defer(ephemeral=True)

    try:
        # 1. 獲取 Entitlement Token
        ent_res = requests.post(
            "https://entitlements.auth.riotgames.com/api/v1/entitlements/token",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        
        if ent_res.status_code != 200:
            await interaction.followup.send("❌ 網址解析失敗或已過期！請重新對照教學步驟，並確認有『完整複製』整條長網址。")
            return
            
        entitlement_token = ent_res.json()["entitlements_token"]

        # 2. 向 Riot 商店接口請求資料
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Riot-Entitlements-JWT": entitlement_token,
            "X-Riot-ClientVersion": "release-08.11-shipping-16-2454652",
            "X-Riot-ClientPlatform": "ew0KCSJjbGllbnRQbGF0Zm9ybSI6ICJXaW5kb3dzIiwNCgljbGllbnRQbGF0Zm9ybVZlcnNpb24iOiAiMTBHLjAuMTkwNDIuMS4yNTYuNjQiLA0KCWNsaWVudFBsYXRmb3JtU3Vic3lzdGVtIjogIk5vbmUiLA0KCWNsaWVudFBsYXRmb3JtQ2hpcHNldCI6ICJVbmtub3duIg0KfQ=="
        }

        shop_res = requests.get(f"https://pd.ap.a.pvp.net/store/v2/store/{user_id}", headers=headers)
        
        if shop_res.status_code == 200:
            shop_data = shop_res.json()
            skin_uuids = shop_data["SkinsPanelLayout"]["SingleItemOffers"]
            
            embeds = []
            main_embed = discord.Embed(
                description="✨ **每日商店查詢成功！**\n*(新商店於台灣時間明早 8 點更新)*",
                color=0xFFFFFF
            )
            embeds.append(main_embed)

            for uuid in skin_uuids:
                name, icon_url = get_skin_data(uuid)
                item_embed = discord.Embed(title=name, color=0x2B2D31)
                item_embed.set_thumbnail(url=icon_url)
                embeds.append(item_embed)

            await interaction.followup.send(embeds=embeds)
        else:
            await interaction.followup.send(f"❌ 查詢失敗，Token 可能已失效，請重新獲取網址。（錯誤碼：{shop_res.status_code}）")

    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("❌ 錯誤：找不到環境變數 BOT_TOKEN！")
