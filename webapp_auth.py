import asyncio
from urllib.parse import unquote
from pathlib import Path
from telethon import TelegramClient, functions, types
from config import (
    DEFAULT_API_ID,
    DEFAULT_API_HASH,
    BOT_USERNAME,
    BOT_APP_NAME,
    DEVICE_MODEL,
    SYSTEM_VERSION,
    APP_VERSION
)

async def extract_init_data(session_path: Path, api_id=DEFAULT_API_ID, api_hash=DEFAULT_API_HASH) -> str:
    """
    Telethon sessiya faylidan @XsollaRewardsBot WebApp uchun kerakli
    initData (tgWebAppData) avtorizatsiya qatorini oladi.
    """
    session_file_name = session_path.stem if session_path.suffix == '.session' else session_path.name
    client = TelegramClient(
        str(session_path.parent / session_file_name),
        api_id,
        api_hash,
        device_model=DEVICE_MODEL,
        system_version=SYSTEM_VERSION,
        app_version=APP_VERSION,
        lang_code="en",
        system_lang_code="en"
    )
    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        raise ValueError(f"Sessiya avtorizatsiyadan o'tmagan yoki muddati tugagan: {session_path.name}")

    try:
        bot = await client.get_input_entity(BOT_USERNAME)
        
        # 1. Start komandasini yuborish (agar bot bilan chat bo'lmagan bo'lsa)
        try:
            await client.send_message(bot, "/start")
            await asyncio.sleep(1)
        except Exception:
            pass

        url = None
        
        # 2. WebApp URL olishga urinish (RequestAppWebViewRequest)
        try:
            res = await client(functions.messages.RequestAppWebViewRequest(
                peer=bot,
                app=types.InputBotAppShortName(bot_id=bot, short_name=BOT_APP_NAME),
                platform="android",
                write_allowed=True
            ))
            url = res.url
        except Exception:
            # 3. Agar short_name orqali bo'lmasa, umumiy RequestWebViewRequest orqali urinish
            try:
                res = await client(functions.messages.RequestWebViewRequest(
                    peer=bot,
                    bot=bot,
                    platform='android',
                    from_bot_menu=False,
                    url='https://rewards.xsolla.com'
                ))
                url = res.url
            except Exception as ex:
                raise RuntimeError(f"WebApp URL olinmadi: {str(ex)}")

        await client.disconnect()

        if not url:
            raise RuntimeError("Telegram botdan WebApp URL bo'sh qaytdi.")

        # URL dan tgWebAppData (initData) ni ajratib olish
        init_data = ""
        if "#tgWebAppData=" in url:
            part = url.split("#tgWebAppData=")[1].split("&tgWebAppVersion=")[0].split("&tgWebAppPlatform=")[0]
            init_data = unquote(part)
        elif "tgWebAppData=" in url:
            part = url.split("tgWebAppData=")[1].split("&")[0]
            init_data = unquote(part)
        else:
            init_data = url

        return init_data

    except Exception as e:
        if client.is_connected():
            await client.disconnect()
        raise e
