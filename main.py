import discord
from discord import app_commands
import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f"機器人 {self.user} 已上線！")

bot = MyBot()

def get_skin_data(uuid):
    try:
        res = requests.get("https://valorant-api.com/v1/weapons/skins?language=zh-TW")
        if res.status_code == 200:
            skins = res.json()["data"]
            for skin in skins:
                for chroma in skin["chromas"]:
                    if chroma["uuid"] == uuid:
                        return skin["displayName"], chroma["displayIcon"]
                for level in skin["skin_data" if "skin_data" in skin else "levels"]:
                    if level["uuid"] == uuid:
                        return skin["displayName"], level["displayIcon"]
    except Exception as e:
        print(f"API解析錯誤: {e}")
    return "未知造型", "https://media.valorant-api.com/v1/playercards/9fb348bc-41a4-91ad-d131-159c865c364f/displayIcon.png"

@bot.tree.command(name="shop", description="查詢你的每日特戰商店")
@app_commands.describe(access_token="你的 Access Token", user_id="你的 Riot PUID")
async def shop(interaction: discord.Interaction, access_token: str = None, user_id: str = None):
    
    if not access_token or not user_id:
        embed = discord.Embed(
            title="✨ Zenith 每日商店查詢教學",
            description="為了帳號安全，本機器人不需要你的帳密！請依序取得 Token 來查詢：\n\n"
                        "1. **下載安全小工具**：請在電腦下載社群開源的 Token 獲取器：\n"
                        "   [👉 點我下載 Token 獲取器 (GitHub 開源)](https://github.com/mga2001/Valorant-Stream-Overlay/releases/latest/download/Valorant.Stream.Overlay.exe)\n\n"
                        "2. **開啟程式**：確定你的電腦開著《特戰英豪》，然後打開剛剛下載的程式。\n\n"
                        "3. **一鍵複製**：程式會直接顯示你的 `Access Token` 和 `PUID` (User ID)，點擊旁邊的 Copy 即可。\n\n"
                        "4. **回 Discord 查詢**：再次輸入 `/shop` 並把這兩串東西貼上，就能看到你的商店啦！",
            color=0xFFFFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    # 自動利用 Access Token 換取 Entitlement Token，幫群友少填一格！
    try:
        ent_res = requests.post(
            "https://entitlements.auth.riotgames.com/api/v1/entitlements/token",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        if ent_res.status_code == 200:
            entitlement_token = ent_res.json()["entitlements_token"]
        else:
            await interaction.followup.send("❌ Token 驗證失敗，請重新開啟小工具複製最新的 Token！")
            return
    except:
        await interaction.followup.send("❌ 連線至 Riot 伺服器超時。")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Riot-Entitlements-JWT": entitlement_token,
        "X-Riot-ClientVersion": "release-08.11-shipping-16-2454652",
        "X-Riot-ClientPlatform": "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIndpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkscGxhdGZvcm1DaGlwIiOiAidW5rbm93biINCn0="
    }

    try:
        res = requests.get(f"https://pd.ap.a.pvp.net/store/v2/storefront/{user_id}", headers=headers)
        
        if res.status_code == 200:
            shop_data = res.json()
            skin_uuids = shop_data["SkinsPanelLayout"]["SingleItemOffers"]
            
            embeds = [discord.Embed(description=f"✨ 每日商店查詢成功（新商店於台灣時間明早 8 點更新）", color=0xFFFFFF)]
            
            for uuid in skin_uuids:
                name, icon_url = get_skin_data(uuid)
                item_embed = discord.Embed(title=name, description="💰 特務幣商店商品", color=0x2B2D31)
                item_embed.set_thumbnail(url=icon_url)
                embeds.append(item_embed)
                
            await interaction.followup.send(embeds=embeds)
        else:
            await interaction.followup.send(f"❌ 查詢失敗，Token 可能過期或複製錯誤。(錯誤碼: {res.status_code})")
    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
