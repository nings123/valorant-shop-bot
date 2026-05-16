import discord
from discord import app_commands
import requests
import os

# 讀取機器人 Token
BOT_TOKEN = os.environ.get("BOT_TOKEN")

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        await self.tree.sync()
        print(f"機器人 {self.user} 已上線並完成指令同步！")

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

# 註冊 /shop 指令
@bot.tree.command(name="shop", description="查詢你的每日特戰商店")
@app_commands.describe(entitlement_token="你的 Entitlement Token", access_token="你的 Access Token", user_id="你的 Riot PUID")
async def shop(interaction: discord.Interaction, entitlement_token: str = None, access_token: str = None, user_id: str = None):
    
    # 如果沒輸入 Token，機器人會先跳出教學指導
    if not entitlement_token or not access_token or not user_id:
        embed = discord.Embed(
            title="🔒 如何安全地查詢每日商店？",
            description="為了帳號安全，本機器人不需要你的帳密！請依序取得 Token 來查詢：\n\n"
                        "1. 登入 [Riot 官方網站](https://auth.riotgames.com/)\n"
                        "2. 開啟另一個分頁，複製並前往以下三個網址取得代碼：\n"
                        "   • Access Token: `https://auth.riotgames.com/authorize?client_id=play-valorant-web-prod&response_type=token%20id_token&redirect_uri=https%3A%2F%2Fplayvalorant.com%2Fopt_in`\n"
                        "   • Entitlement: `https://entitlements.auth.riotgames.com/api/v1/entitlements/token`\n"
                        "   • User ID: `https://auth.riotgames.com/userinfo`\n\n"
                        "3. 取得後，使用 `/shop [entitlement_token] [access_token] [user_id]` 查詢！",
            color=0xFFFFFF # 簡約全白邊條
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # 延遲回應，因為抓取資料需要時間
    await interaction.response.defer(ephemeral=True)

    # 呼叫 Riot 官方商店 API
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Riot-Entitlements-JWT": entitlement_token,
        "X-Riot-ClientVersion": "release-08.05-shipping-21-2384240",
        "X-Riot-ClientPlatform": "ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIndpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkscGxhdGZvcm1DaGlwIiOiAidW5rbm93biINCn0="
    }

    try:
        # 抓取每日商店商品的 UUID
        res = requests.get(f"https://pd.ap.a.pvp.net/store/v2/storefront/{user_id}", headers=headers)
        
        if res.status_code == 200:
            shop_data = res.json()
            skin_uuids = shop_data["SkinsPanelLayout"]["SingleItemOffers"]
            
            # 建立精美的卡片排版
            embeds = [discord.Embed(description=f"✨ 每日商店查詢成功（新商店於台灣時間明早 8 點更新）", color=0xFFFFFF)]
            
            for uuid in skin_uuids:
                name, icon_url = get_skin_data(uuid)
                item_embed = discord.Embed(title=name, description="💰 特務幣商店商品", color=0x2B2D31) # 深色背景
                item_embed.set_thumbnail(url=icon_url)
                embeds.append(item_embed)
                
            await interaction.followup.send(embeds=embeds)
            
        else:
            await interaction.followup.send(f"❌ 查詢失敗，Token 可能過期了，請重新獲取！(錯誤碼: {res.status_code})")
    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("錯誤：找不到 BOT_TOKEN")
