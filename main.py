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
    print(f"🤖 機器人 {bot.user} 已上線，超完美一鍵商店查詢就緒！")

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

# Discord 斜線指令：/shop
@bot.tree.command(name="shop", description="查詢你的每日特戰商店")
@app_commands.describe(
    access_token="直接貼上點開連結後，最上方網址列的『整條完整長網址』", 
    user_id="此欄位『完全不用填』，留空即可！"
)
async def shop(interaction: discord.Interaction, access_token: str, user_id: str = None):
    
    # 【超級防呆解析】不論群友是填單一 Token 還是直接丟整條長網址，通通在後端自動切開
    if "access_token=" in access_token or "login.live.com" in access_token:
        url_input = access_token
        access_match = re.search(r'access_token=([^&]+)', url_input)
        id_token_match = re.search(r'id_token=([^&]+)', url_input)
        
        if access_match:
            access_token = access_match.group(1)
            # 自動從 id_token 解碼出使用者的 Riot PUID (user_id)
            if id_token_match:
                try:
                    payload_b64 = id_token_match.group(1).split('.')[1]
                    payload_b64 += '=' * (-len(payload_b64) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
                    user_id = payload.get('sub')
                except:
                    pass

    # 如果欄位沒帶對，或根本沒填，就噴出超漂亮的防呆教學卡片
    if not access_token or not user_id:
        embed = discord.Embed(
            title="✨ 每日商店查詢教學",
            description=(
                "為了帳號安全，本群不收集任何密碼。請依序點擊官方認證通道：\n\n"
                "1️⃣ **第一步：登入官網**\n"
                "請先用瀏覽器登入 [👉 Riot 官方帳號管理中心](https://account.riotgames.com/)\n"
                "*(必須確認看到自己的 Riot ID 登入成功喔！)*\n\n"
                "2️⃣ **第二步：一鍵獲取 Token（用電腦點擊）**\n"
                "登入成功後**不要關閉網頁**，直接點擊下方安全通道按鈕。它會開啟官方認證，並彈出一個微軟的空白網頁，這代表完全成功！\n"
                "[🔗 點我一鍵獲取安全 Token](https://auth.riotgames.com/authorize?client_id=play-valorant-web-prod&response_type=token+id_token&redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf&scope=openid+link+ban&nonce=1)\n\n"
                "3️⃣ **第三步：複製網址並貼回查詢**\n"
                "請把那個微軟網頁最上方網址列的**「整條完整長網址」全部複製起來**。\n\n"
                "再次回到 Discord 輸入 `/shop`，直接把網址貼在 `access_token` 第一個框框，**第二個框框完全不用填**，直接按下 Enter 送出即可！"
            ),
            color=0xFFFFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # 進入查詢流程
    await interaction.response.defer(ephemeral=True)

    try:
        # 1. 獲取 Entitlement Token
        ent_res = requests.post(
            "https://entitlements.auth.riotgames.com/api/v1/entitlements/token",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        
        if ent_res.status_code != 200:
            await interaction.followup.send("❌ 網址解析失敗或已過期！請確認是否有『完整複製』整條長網址，並重新嘗試。")
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
            await interaction.followup.send(f"❌ 查詢失敗，Token 可能已失效，請重新點擊連結複製網址。（錯誤碼：{shop_res.status_code}）")

    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("❌ 錯誤：找不到環境變數 BOT_TOKEN！")
