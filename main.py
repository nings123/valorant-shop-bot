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
                for level in skin["levels"]:
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
                        "1. **前往專屬網頁**：請點擊下方連結前往安全解析網頁：\n"
                        "   [👉 點我前往 Zenith Token 獲取助手](https://nings123.github.io/valorant-shop-bot/)\n\n"
                        "2. **獲取 Token**：在網頁中點擊登入 Riot 官方帳號。登入成功後，將瀏覽器最上方的「完整網址列」全部複製，並貼回網頁的輸入框中，即可一鍵產出對應金鑰！\n\n"
                        "3. **一鍵複製**：點擊網頁上的複製按鈕，分別獲取 `Access Token` 和 `User ID`。\n\n"
                        "4. **回 Discord 查詢**：再次輸入 `/shop` 並把這兩串東西對應貼上，就能秒出你的商店卡片啦！",
            color=0xFFFFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    try:
        ent_res = requests.post(
            "https://entitlements.auth.riotgames.com/api/v1/entitlements/token",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        if ent_res.status_code == 200:
            entitlement_token = ent_res.json()["entitlements_token"]
        else:
            await interaction.followup.send("❌ Token 驗證失敗，請確認是否複製完整，或重新開啟小工具獲取新 Token！")
            return
    except:
        await interaction.followup.send("❌ 連線至 Riot 驗證伺服器超時。")
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
            await interaction.followup.send(f"❌ 查詢失敗，Token 可能過期了。(錯誤碼: {res.status_code})")
    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
