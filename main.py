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
                        return skin["displayName"], level["withonedIcon" if "withonedIcon" in level else "displayIcon"]
    except Exception as e:
        print(f"API解析錯誤: {e}")
    return "未知造型", "https://media.valorant-api.com/v1/playercards/9fb348bc-41a4-91ad-d131-159c865c364f/displayIcon.png"

@bot.tree.command(name="shop", description="查詢你的每日特戰商店")
@app_commands.describe(entitlement_token="防空免填", access_token="你的 Access Token", user_id="你的 Riot PUID")
async def shop(interaction: discord.Interaction, entitlement_token: str = None, access_token: str = None, user_id: str = None):
    
    # 💡 這裡請把網址改成你剛剛在 第三步 拿到的 GitHub Pages 專屬網址！
    MY_WEB_URL = "https://nings123.github.io/valorant-shop-bot/"

    if not access_token or not user_id:
        embed = discord.Embed(
            title="✨ Zenith 每日商店查詢教學",
            description=f"為了帳號安全，本群不收集密碼。請點擊下方連結一鍵獲取：\n\n"
                        f"[👉 點我前往 Zenith 專屬金鑰獲取網頁]({MY_WEB_URL})\n\n"
                        f"1. 點擊網頁中的「官方授權登入」並完成登入。\n"
                        f"2. 登入後網頁會直接彈出代碼，點擊即可一鍵複製。\n"
                        f"3. 回到 Discord 輸入 `/shop` 填入對應欄位即可查詢！",
            color=0xFFFFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    # 2026 最新機制：其實只要有 Access Token，機器人就能自己去跟 Riot 換取 Entitlement！群友連第三個網址都不用開了！
    try:
        ent_res = requests.post(
            "https://entitlements.auth.riotgames.com/api/v1/entitlements/token",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        if ent_res.status_code == 200:
            entitlement_token = ent_res.json()["entitlements_token"]
        else:
            await interaction.followup.send("❌ 憑證自動換取失敗，請重新前往網頁登入獲取新 Token！")
            return
    except:
        await interaction.followup.send("❌ 連線驗證伺服器失敗。")
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
            await interaction.followup.send(f"❌ 查詢失敗，Token 可能過期了！(錯誤碼: {res.status_code})")
    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

if __name__ == "__main__":
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
