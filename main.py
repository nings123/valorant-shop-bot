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
        # 讓斜線指令與 Discord 伺服器同步
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"🤖 機器人 {bot.user} 已上線！")
    print("✨ 專屬網頁版商店查詢與全自動防呆解析機制已就緒！")

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
    # 若找不到圖片，提供預設的特戰卡面作為後備
    return "未知造型", "https://media.valorant-api.com/v1/playercards/9fb348bc-41a4-91ad-d131-159c865c364f/displayIcon.png"

# Discord 斜線指令：/shop (將兩個參數都設為選填 None)
@bot.tree.command(name="shop", description="查詢你的每日特戰商店")
@app_commands.describe(
    access_token="貼上從 Zenith 助手網頁獲取到的『整條長網址』，第一次使用請留空送出看教學", 
    user_id="此欄位『完全不用填』，留空即可！"
)
async def shop(interaction: discord.Interaction, access_token: str = None, user_id: str = None):
    
    # 🌟【超強全自動解析】只要群友貼進來的是整條網址（包含 github、login.live 或 access_token 關鍵字）
    if access_token and ("access_token=" in access_token or "github.io" in access_token or "login.live.com" in access_token):
        url_input = access_token
        # 正則表達式抓取網址中的 access_token 與 id_token
        access_match = re.search(r'access_token=([^&]+)', url_input)
        id_token_match = re.search(r'id_token=([^&]+)', url_input)
        
        if access_match:
            access_token = access_match.group(1)
            # 全自動從 id_token 中解碼出使用者的 Riot PUID (user_id)
            if id_token_match:
                try:
                    payload_b64 = id_token_match.group(1).split('.')[1]
                    payload_b64 += '=' * (-len(payload_b64) % 4)
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
                    user_id = payload.get('sub')
                except:
                    pass

    # 💡【防呆教學機制】如果群友什麼都沒填（第一次用），或者網址沒帶對，直接彈出專屬網頁教學
    if not access_token or not user_id:
        embed = discord.Embed(
            title="✨特戰每日商店查詢助手",
            description=(
                "為了保障您的帳號安全，本群機器人**絕不收集或索取您的帳號密碼**。 🛡️\n\n"
                "我們已經為社群建立專屬的快速安全獲取工具！請點擊下方網頁，只要登入後點擊「一鍵安全授權」，網頁就會幫你自動生成 Token 網址喔：\n\n"
                "[🌐 點我前往 Zenith 專屬 Token 獲取網頁](https://nings123.github.io/valorant-shop-bot/)\n\n"
                "在網頁拿到網址並複製後，重新回到 Discord 輸入 `/shop` 並貼在 `access_token` 欄位（第二格留空），按下 Enter 就能秒出你的商店造型啦！"
            ),
            color=0xFFFFFF
        )
        # 使用 ephemeral=True 讓這條教學訊息只有輸入指令的群友自己看得到，保持頻道整潔
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # 進入正式的商店查詢流程
    await interaction.response.defer(ephemeral=True)

    try:
        # 1. 向 Riot 驗證伺服器獲取 Entitlement Token
        ent_res = requests.post(
            "https://entitlements.auth.riotgames.com/api/v1/entitlements/token",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        
        if ent_res.status_code != 200:
            await interaction.followup.send("❌ 網址金鑰已過期或複製不完整！請重新前往網頁獲取新網址。")
            return
            
        entitlement_token = ent_res.json()["entitlements_token"]

        # 2. 封裝 Riot API 請求標頭
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Riot-Entitlements-JWT": entitlement_token,
            "X-Riot-ClientVersion": "release-08.11-shipping-16-2454652",
            "X-Riot-ClientPlatform": "ew0KCSJjbGllbnRQbGF0Zm9ybSI6ICJXaW5kb3dzIiwNCgljbGllbnRQbGF0Zm9ybVZlcnNpb24iOiAiMTBHLjAuMTkwNDIuMS4yNTYuNjQiLA0KCWNsaWVudFBsYXRmb3JtU3Vic3lzdGVtIjogIk5vbmUiLA0KCWNsaWVudFBsYXRmb3JtQ2hpcHNldCI6ICJVbmtub3duIg0KfQ=="
        }

        # 3. 向 AP 亞太地區伺服器請求每日商店
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

            # 走訪四個每日商店的造型 UUID，拉取名字與圖片
            for uuid in skin_uuids:
                name, icon_url = get_skin_data(uuid)
                item_embed = discord.Embed(title=name, color=0x2B2D31)
                item_embed.set_thumbnail(url=icon_url)
                embeds.append(item_embed)

            # 發送精美的多卡片商店訊息
            await interaction.followup.send(embeds=embeds)
        else:
            await interaction.followup.send(f"❌ 查詢失敗，金鑰可能已失效，請重新進入網頁獲取。（錯誤碼：{shop_res.status_code}）")

    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

# 啟動機器人
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("❌ 錯誤：找不到環境變數 BOT_TOKEN！")
