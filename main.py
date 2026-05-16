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
        # 改用最新、最穩定的全球造型全庫 API，修復「未知造型」問題
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
@app_commands.describe(entitlement_token="你的 Entitlement Token", access_token="你的 Access Token", user_id="你的 Riot PUID")
async def shop(interaction: discord.Interaction, entitlement_token: str = None, access_token: str = None, user_id: str = None):
    
    # 如果沒輸入 Token，跳出保證能順利登入的安全通道指南
    if not entitlement_token or not access_token or not user_id:
        embed = discord.Embed(
            title="✨ 每日商店查詢教學",
            description="為了帳號安全，本群不收集密碼。請用以下純官方、保證不壞的方式取得金鑰：\n\n"
                        "1. **第一步：先登入官網**\n"
                        "   請先用電腦瀏覽器開啟並登入 [👉 Riot 官方帳號管理中心](https://account.riotgames.com/)\n"
                        "   *(請務必確保在這個網頁看到自己的 Riot ID 登入成功喔！)*\n\n"
                        "2. **第二步：獲取 Access Token & User ID**\n"
                        "   登入成功後，**不要關閉網頁**，直接在同一個瀏覽器開新分頁，點擊前往這個網址：\n"
                        "   [👉 點我前往官方安全通道網址](https://auth.riotgames.com/authorize?client_id=riot-client&redirect_uri=http%3A%2F%2Flocalhost%2Fredirect&response_type=token%20id_token&scope=openid%20link%20accounts&nonce=1)\n"
                        "   • *注意：點過去畫面顯示「localhost 拒絕連線」是完全正常的！*\n"
                        "   • 請直接看最上方的**網址列**，複製裡面 `access_token=` 後面那一長串亂碼。\n"
                        "   • 網址列中 `sub=` 後面那串英數數字就是你的 **User ID**。\n\n"
                        "3. **第三步：獲取 Entitlement**\n"
                        "   同樣在同個瀏覽器再開一個新分頁，前往以下網址：\n"
                        "   [👉 點我前往 Entitlement 網址](https://entitlements.auth.riotgames.com/api/v1/entitlements/token)\n"
                        "   • 畫面中 `" '"entitlements_token":"...' "` 雙引號裡面的長代碼就是 **Entitlement**。\n\n"
                        "4. **回 Discord 查詢**：再次輸入 `/shop` 並把這三串東西貼上，就能秒出你的簡約風商店卡片啦！",
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
