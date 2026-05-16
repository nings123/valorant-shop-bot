import discord
from discord import app_commands
import requests
import os
import re
import base64
import json

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
    print(f"🤖 {bot.user} 已上線！專屬網頁版商店查詢就緒！")

def get_skin_data(uuid):
    try:
        res = requests.get("https://valorant-api.com/v1/weapons/skins?language=zh-TW")
        if res.status_code == 200:
            skins = res.json()["data"]
            for skin in skins:
                for chroma in skin["chromas"]:
                    if chroma["uuid"] == uuid: return skin["displayName"], chroma["displayIcon"]
                for level in skin["levels"]:
                    if level["uuid"] == uuid: return skin["displayName"], level["displayIcon"]
    except: pass
    return "未知造型", "https://media.valorant-api.com/v1/playercards/9fb348bc-41a4-91ad-d131-159c865c364f/displayIcon.png"

@bot.tree.command(name="shop", description="查詢你的每日特戰商店")
@app_commands.describe(
    access_token="貼上從 Zenith 助手網頁獲取到的『整條長網址』", 
    user_id="此欄位完全不用填，留空即可！"
)
async def shop(interaction: discord.Interaction, access_token: str = None, user_id: str = None):
    
    # 自動解析群友丟進來的整條網址
    if access_token and ("access_token=" in access_token or "login.live.com" in access_token or "github.io" in access_token):
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
                except: pass

    # 🔥 如果沒填參數，就噴出引導群友去你 GitHub Pages 網頁的精美卡片
    if not access_token or not user_id:
        embed = discord.Embed(
            title="✨特戰每日商店查詢助手",
            description=(
                "為了保障您的帳號安全，本群機器人**絕不索取帳號密碼**。 🛡_ \n\n"
                "請點擊下方我們的專屬安全網頁，裡面有手把手一鍵獲取教學，用電腦點擊兩下就能完成喔！\n\n"
                f"[🌐 點我前往 Zenith 專屬 Token 獲取網頁](https://nings123.github.io/valorant-shop-bot/)\n\n"
                "進入網頁拿到網址後，再次回來輸入 `/shop` 並把整條網址貼在 `access_token` 即可查詢！"
            ),
            color=0xFFFFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        ent_res = requests.post(
            "https://entitlements.auth.riotgames.com/api/v1/entitlements/token",
            headers={"Authorization": f"Bearer {access_token}"}, json={}
        )
        if ent_res.status_code != 200:
            await interaction.followup.send("❌ 網址失效或複製不完整！請重新前往網頁獲取新網址。")
            return
            
        entitlement_token = ent_res.json()["entitlements_token"]

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
            main_embed = discord.Embed(description="✨ **每日商店查詢成功！**", color=0xFFFFFF)
            embeds.append(main_embed)

            for uuid in skin_uuids:
                name, icon_url = get_skin_data(uuid)
                item_embed = discord.Embed(title=name, color=0x2B2D31)
                item_embed.set_thumbnail(url=icon_url)
                embeds.append(item_embed)

            await interaction.followup.send(embeds=embeds)
        else:
            await interaction.followup.send("❌ 查詢失敗，Token 可能已過期。")

    except Exception as e:
        await interaction.followup.send(f"❌ 系統錯誤：{str(e)}")

if BOT_TOKEN: bot.run(BOT_TOKEN)
