import discord
from discord import app_commands
import requests
import os

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
    print(f"🤖 機器人 {bot.user} 已上線，一鍵商店查詢就緒！")

# 獲取武器皮膚資料
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
    access_token="輸入複製好的 Access Token (通常是 ey... 開頭的長字串)", 
    user_id="輸入複製好的 User ID (PUID)"
)
async def shop(interaction: discord.Interaction, access_token: str = None, user_id: str = None):
    
    # 只要缺少任何一個欄位，就跳出精心排版、絕對不會壞的一鍵獲取教學
    if not access_token or not user_id:
        embed = discord.Embed(
            title="✨ 每日商店查詢教學",
            description=(
                "為了帳號安全，本群不收集任何密碼。請依序點擊下方官方安全通道：\n\n"
                "1️⃣ **第一步：登入官網**\n"
                "請先點擊前往完成登入（看到自己的 Riot ID 即可）：\n"
                "[👉 點我前往 Riot 官方登入](https://account.riotgames.com/)\n\n"
                "2️⃣ **第二步：一鍵獲取 Token（用電腦點擊）**\n"
                "登入後**不要關閉分頁**，直接點擊下方安全通道。它會開啟官方認證分頁，並直接把你要的程式碼顯示在畫面上，**完全不會跳出 404！**\n"
                "[🔗 點我一鍵獲取安全 Token](https://auth.riotgames.com/authorize?client_id=play-valorant-web-prod&response_type=token+id_token&redirect_uri=https%3A%2F%2Fplayvalorant.com%2Fopt_in&scope=openid+link+ban&nonce=1)\n\n"
                "3️⃣ **第三步：複製並貼回查詢**\n"
                "點過去後，請看瀏覽器最上方的**網址列**，你會看到一長串網址：\n"
                "❌ **不要管網頁畫面寫什麼！** 我們只要複製網址列裡面的關鍵字：\n\n"
                "◽ 複製 `access_token=` 後面到 `&` 之間的那串超長字串（以 `ey` 開頭）。\n"
                "◽ 複製 `sub=` 後面那串英數混合的短字串（這就是你的 User ID）。\n\n"
                "再次回到 Discord 輸入 `/shop` 並貼上這兩串數值，就能秒出商店卡片啦！"
            ),
            color=0xFFFFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # 進入查詢流程
    await interaction.response.defer(ephemeral=True)

    try:
        # 清除可能不小心複製到的網址前後贅詞
        if "access_token=" in access_token:
            import re
            match = re.search(r'access_token=([^&]+)', access_token)
            if match: access_token = match.group(1)
            
        if "sub=" in user_id:
            import re
            match = re.search(r'sub=([^&]+)', user_id)
            if match: user_id = match.group(1)

        # 1. 獲取 Entitlement Token
        ent_res = requests.post(
            "https://entitlements.auth.riotgames.com/api/v1/entitlements/token",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        
        if ent_res.status_code != 200:
            await interaction.followup.send("❌ Token 驗證失敗！請確認是否複製完整，或是 Token 已經過期，請重新點擊連結獲取。")
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
            await interaction.followup.send(f"❌ 查詢失敗，Riot 伺服器拒絕請求。（錯誤碼：{shop_res.status_code}）")

    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("❌ 錯誤：找不到環境變數 BOT_TOKEN！")
