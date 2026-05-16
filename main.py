# 如果沒輸入 Token，跳出全新、保證不會 404 的啟動器通道指南
    if not entitlement_token or not access_token or not user_id:
        embed = discord.Embed(
            title="✨ Zenith 每日商店查詢教學",
            description="為了帳號安全，本群不收集密碼。請用以下純官方、保證不壞的方式取得金鑰：\n\n"
                        "1. **登入官網**：用電腦瀏覽器開啟並登入 [👉 Riot 官方網站](https://auth.riotgames.com/)\n"
                        "2. **獲取 Access Token & User ID**：登入後，在同瀏覽器開新分頁前往以下網址（這是模擬特戰啟動器的安全通道）：\n"
                        "   [👉 點我前往全新不開天窗跳轉網址](https://auth.riotgames.com/authorize?client_id=riot-client&redirect_uri=http%3A%2F%2Flocalhost%2Fredirect&response_type=token%20id_token&scope=openid%20link%20accounts)\n\n"
                        "   *注意：點過去如果畫面顯示「無法連線至網站」或空白是完全正常的！請直接看最上方的**網址列**：*\n"
                        "   • 網址列中 `access_token=` 後面那一長串就是 **Access Token**。\n"
                        "   • 網址列中 `sub=` 後面那串英數就是你的 **User ID**。\n\n"
                        "3. **獲取 Entitlement**：再開一個新分頁前往以下網址：\n"
                        "   [👉 點我前往 Entitlement 網址](https://entitlements.auth.riotgames.com/api/v1/entitlements/token)\n"
                        "   • 畫面中 `" '"entitlements_token":"...' "` 雙引號裡面的長代碼就是 **Entitlement**。\n\n"
                        "4. **回 Discord 查詢**：再次輸入 `/shop` 並把這三串東西貼上，就能秒出你的黑白商店卡片啦！",
            color=0xFFFFFF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
