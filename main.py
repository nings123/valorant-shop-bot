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
        res = requests.get(f"https://valorant-api.com/v1/weapons/skinlevels/{uuid}?language=zh-TW")
        if res.status_code == 200:
            data = res.json()["data"]
            return data["displayName"], data["displayIcon"]
    except:
        pass
    return "未知造型", "https://media.valorant-api.com/v1/playercards/9fb348bc-41a4-91ad-d131-159c865c364f/displayIcon.png"

@bot.tree.command(name="shop", description="查詢你的每日特戰商店")
@app_commands.describe(entitlement_token="你的 Entitlement Token", access_token="你的 Access Token", user_id="你的 Riot PUID")
async def shop(interaction: discord.Interaction, entitlement_token: str = None, access_token: str = None, user_id: str = None):
    
    # 如果沒輸入，跳出全新的無腦網頁獲取指南
    if not entitlement_token or not access_token or not user_id:
        embed = discord.Embed(
            title="✨ Zenith 每日商店查詢教學",
            description="為了帳號安全，本群不收集密碼。請用以下最簡單的方式取得金鑰：\n\n"
                        "1. **打開登入網頁**：請點擊下方安全連結進行 Riot 官方授權登入：\n"
                        "   [👉 點我前往 Riot 安全登入網頁](https://auth.solv3.de/)\n"
                        "2. **一鍵複製**：登入成功後，網頁會直接顯示這三串東西，請直接點擊它們一鍵複製。\n\n"
                        "3. **回 Discord 查詢**：再次在頻道輸入 `/shop`，並把複製好的 `Access Token`、`Entitlement` 和 `User ID` 貼上，就能秒出你的黑白商店卡片啦！",
            color=0xFFFFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

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
            await interaction.followup.send(f"❌ 查詢失敗，代碼可能打錯或過期了！(錯誤碼: {res.status_code})")
    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
