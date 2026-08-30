import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import asyncio
from pathlib import Path
from telethon import TelegramClient, events
from rich.console import Console
from rich.panel import Panel
from config import (
    SESSIONS_DIR,
    DEFAULT_API_ID,
    DEFAULT_API_HASH,
    DEVICE_MODEL,
    SYSTEM_VERSION,
    APP_VERSION
)

console = Console(force_terminal=True, legacy_windows=False)

def get_client(session_path: Path):
    session_file_name = session_path.stem if session_path.suffix == '.session' else session_path.name
    return TelegramClient(
        str(session_path.parent / session_file_name),
        DEFAULT_API_ID,
        DEFAULT_API_HASH,
        device_model=DEVICE_MODEL,
        system_version=SYSTEM_VERSION,
        app_version=APP_VERSION,
        lang_code="en",
        system_lang_code="en"
    )

async def check_recent_messages(client):
    """Oxirgi kelgan Telegram login kodlarini o'qiydi"""
    try:
        # Telegram rasmiy bildirishnomalari (777000 yoki Service Notifications)
        async for message in client.iter_messages(777000, limit=5):
            console.print(Panel.fit(
                f"[bold yellow]📩 Telegramdan kelgan oxirgi xabar:[/bold yellow]\n\n"
                f"[bold white]{message.text}[/bold white]\n\n"
                f"[dim]Vaqt: {message.date}[/dim]",
                title="Telegram Login Kodi",
                border_style="green"
            ))
            return
    except Exception as e:
        console.print(f"[dim]Eski xabarlarni olishda: {str(e)}[/dim]")

async def listen_for_codes(session_name: str):
    session_file = SESSIONS_DIR / f"{session_name}.session" if not session_name.endswith(".session") else SESSIONS_DIR / session_name
    
    if not session_file.exists():
        console.print(f"[bold red]❌ Sessiya topilmadi: {session_file.name}[/bold red]")
        return

    client = get_client(session_file)
    await client.connect()

    if not await client.is_user_authorized():
        console.print(f"[bold red]❌ Bu sessiya avtorizatsiyadan o'tmagan.[/bold red]")
        await client.disconnect()
        return

    me = await client.get_me()
    console.print(Panel.fit(
        f"[bold green]✅ Telegram akkauntingiz kompyuterda FAOL turibdi![/bold green]\n\n"
        f"👤 Ism: [cyan]{me.first_name}[/cyan]\n"
        f"📞 Telefon: [yellow]{me.phone or 'Mavjud'}[/yellow]\n\n"
        f"[bold yellow]Endi telefoningizda (TeleGraph yoki rasmiy Telegramda) telefon raqamingizni kiriting.[/bold yellow]\n"
        f"[cyan]Telegram kodni ushbu kompyuterga yuboradi va kod shu yerda darhol ko'rinadi![/cyan]",
        title="Telegram Kod Qabul Qiluvchi",
        border_style="cyan"
    ))

    # 1. Oxirgi kelgan xabarni ko'rsatish
    await check_recent_messages(client)

    # 2. Yangi keladigan kodlarni kutish (Real-time listener)
    console.print("[bold cyan]⏳ Yangi Telegram kod kutilmoqda (telefoningizdan login so'rang)...[/bold cyan]")

    @client.on(events.NewMessage(from_users=777000))
    async def handler(event):
        console.print("\n" + "="*50)
        console.print(Panel.fit(
            f"[bold green]🎉 YANGI TELEGRAM KOD KELDI:[/bold green]\n\n"
            f"[bold white]{event.message.text}[/bold white]",
            title="YANGI KOD",
            border_style="bold green"
        ))
        console.print("="*50 + "\n")

    # Kutish rejimida ushlab turish
    await client.run_until_disconnected()

if __name__ == "__main__":
    sessions = list(SESSIONS_DIR.glob("*.session"))
    if not sessions:
        console.print("[red]Hech qanday sessiya fayli topilmadi.[/red]")
        sys.exit(1)

    target_session = sessions[0].stem
    if len(sessions) > 1:
        console.print("Mavjud sessiyalar:")
        for idx, s in enumerate(sessions, 1):
            console.print(f"{idx}. {s.stem}")
        choice = input(f"Qaysi sessiyadan kod olinsin? (standart: {target_session}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(sessions):
            target_session = sessions[int(choice)-1].stem

    asyncio.run(listen_for_codes(target_session))
