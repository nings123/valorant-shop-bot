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
        # 啟動時自動同步斜線指令
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"🤖 機器人 {bot.user} 已上線，隨時準備為您查詢特戰商店！")

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
    # 預設回傳未知造型與字卡
    return "未知造型", "https://media.valorant-api.com/v1/playercards/9fb348bc-41a4-91ad-d131-159c865c364f/displayIcon.png"

# Discord 斜線指令：/shop
@bot.tree.command(name="shop", description="查詢你的每日特戰商店")
@app_commands.describe(access_token="貼上獲取到的 Token 或直接貼上整個 localhost 網址", user_id="你的 Riot PUID (若第一格貼完整網址，此格可不填)")
async def shop(interaction: discord.Interaction, access_token: str, user_id: str = None):
    
    # 【超級防呆機制】如果使用者直接把整條 localhost 網址貼進 access_token 欄位
    if "access_token=" in access_token:
        url_input = access_token
        access_match = re.search(r'access_token=([^&]+)', url_input)
        id_token_match = re.search(r'id_token=([^&]+)', url_input)
        
        if access_match:
            access_token = access_match.group(1)
            # 如果群友貼了完整網址，順便幫他解析出 user_id，他就不用手動輸入兩次了
            if id_token_match:
                try:
                    payload_b64 = id_token_match.group(1).split('.')[1]
                    payload_b64 += '=' * (-len(payload_b64) % 4) # 補齊 base64 填補符
                    payload = json.loads(base64.urlsafe_b64decode(payload_b64).decode('utf-8'))
                    user_id = payload.get('sub')
                except Exception as b64_err:
                    print(f"⚠️ 解析 PUID 失敗: {b64_err}")

    # 如果經過上面解析後，還是缺少必要的欄位，就跳出精美的教學引導
    if not access_token or not user_id:
        embed = discord.Embed(
            title="✨ 每日商店查詢教學",
            description=(
                "為了帳號安全，本群不收集任何密碼。請依序透過官方原生通道取得金鑰：\n\n"
                "1️⃣ **第一步：先登入官網**\n"
                "請先用電腦瀏覽器開啟並登入 [👉 Riot 官方帳號管理中心](https://account.riotgames.com/)\n"
                "*(請務必確保在這個網頁看到自己的 Riot ID 登入成功喔！)*\n\n"
                "2️⃣ **第二步：獲取 Access Token & User ID**\n"
                "登入成功後，**不要關閉網頁**，直接在同一個瀏覽器複製並在網址列貼上打開這串「官方安全通道網址」：\n"
                "```text\n"
                "[https://auth.riotgames.com/authorize?client_id=riot-client&redirect_uri=http%3A%2F%2Flocalhost%2Fredirect&response_type=token+id_token&scope=openid+link+ban&nonce=1](https://auth.riotgames.com/authorize?client_id=riot-client&redirect_uri=http%3A%2F%2Flocalhost%2Fredirect&response_type=token+id_token&scope=openid+link+ban&nonce=1)\n"
                "```\n"
                "👉 *點過去畫面顯示「localhost 拒絕連線」是完全正常的！*\n"
                "請直接複製最上方那整條**「包含 localhost 開頭的完整網址列」**。\n\n"
                "3️⃣ **第三步：回 Discord 查詢**\n"
                "再次輸入 `/shop`，直接把剛剛複製的那整條長網址貼進 `access_token` 第一個框框裡，第二個框框（user_id）留空不用填，按下送出就能秒出你的商店卡片啦！"
            ),
            color=0xFFFFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # 進入查詢流程，先發送延遲回應避免超時
    await interaction.response.defer(ephemeral=True)

    try:
        # 1. 獲取 Entitlement Token
        ent_res = requests.post(
            "https://entitlements.auth.riotgames.com/api/v1/entitlements/token",
            headers={"Authorization": f"Bearer {access_token}"},
            json={}
        )
        
        if ent_res.status_code != 200:
            await interaction.followup.send("❌ Token 驗證失敗，請確認是否完整複製，或重新照教學步驟獲取網址！")
            return
            
        entitlement_token = ent_res.json()["entitlements_token"]

        # 2. 向 Riot 商店接口請求每日商店資料
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Riot-Entitlements-JWT": entitlement_token,
            "X-Riot-ClientVersion": "release-08.11-shipping-16-2454652",  # 保持最新的 Client 版本
            "X-Riot-ClientPlatform": "ew0KCSJjbGllbnRQbGF0Zm9ybSI6ICJXaW5kb3dzIiwNCgljbGllbnRQbGF0Zm9ybVZlcnNpb24iOiAiMTBHLjAuMTkwNDIuMS4yNTYuNjQiLA0KCWNsaWVudFBsYXRmb3JtU3Vic3lzdGVtIjogIk5vbmUiLA0KCWNsaWVudFBsYXRmb3JtQ2hpcHNldCI6ICJVbmtub3duIg0KfQ=="
        }

        # AP 區域代號代表亞太地區（包含台灣）
        shop_res = requests.get(f"https://pd.ap.a.pvp.net/store/v2/store/{user_id}", headers=headers)
        
        if shop_res.status_code == 200:
            shop_data = shop_res.json()
            skin_uuids = shop_data["SkinsPanelLayout"]["SingleItemOffers"]
            
            # 建立精美的商店回覆卡片
            embeds = []
            main_embed = discord.Embed(
                description="✨ **每日商店查詢成功！**\n*(新商店於台灣時間明早 8 點更新)*",
                color=0xFFFFFF
            )
            embeds.append(main_embed)

            # 依序抓取 4 個每日造型
            for uuid in skin_uuids:
                name, icon_url = get_skin_data(uuid)
                item_embed = discord.Embed(title=name, color=0x2B2D31)
                item_embed.set_thumbnail(url=icon_url)
                embeds.append(item_embed)

            await interaction.followup.send(embeds=embeds)
        else:
            await interaction.followup.send(f"❌ 查詢失敗，Token 可能過期了。（錯誤碼：{shop_res.status_code}）")

    except Exception as e:
        await interaction.followup.send(f"❌ 系統發生錯誤：{str(e)}")

# 啟動機器人
if BOT_TOKEN:
    bot.run(BOT_TOKEN)
else:
    print("❌ 錯誤：找不到環境變數 BOT_TOKEN，請檢查設定！")
