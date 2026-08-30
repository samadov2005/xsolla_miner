import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import asyncio
import io
import qrcode
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt
from config import (
    SESSIONS_DIR,
    DEFAULT_API_ID,
    DEFAULT_API_HASH,
    DEVICE_MODEL,
    SYSTEM_VERSION,
    APP_VERSION
)

console = Console(force_terminal=True, legacy_windows=False)

def create_client(session_path: Path):
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

def print_qr_code(url: str):
    """Terminalda QR kodni chiroyli qilib chizadi"""
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    
    f = io.StringIO()
    qr.print_ascii(out=f, invert=True)
    console.print(f"[white]{f.getvalue()}[/white]")

def cleanup_session_file(session_file: Path):
    """Muvaffaqiyatsiz kirilgan bo'lsa, chala .session faylni o'chirib tashlaydi"""
    try:
        actual_file = session_file.with_suffix('.session') if session_file.suffix != '.session' else session_file
        if actual_file.exists():
            actual_file.unlink()
    except Exception:
        pass

async def login_with_qr():
    """QR Kod orqali darhol ulash (Captcha yoki SMS kodi talab qilmaydi)"""
    console.print("\n[bold cyan]📷 QR Kod Orqali Akkaunt Ulash[/bold cyan]")
    acc_name = Prompt.ask("[yellow]Akkaunt uchun nom kiriting (masalan: akk1 yoki telefon raqami)[/yellow]").strip()
    if not acc_name:
        acc_name = "account"
        
    session_file = SESSIONS_DIR / acc_name.replace("+", "").replace(" ", "")
    client = create_client(session_file)
    await client.connect()

    is_logged_in = False
    try:
        if await client.is_user_authorized():
            me = await client.get_me()
            console.print(f"[green]✅ Ushbu akkaunt ({me.first_name}) allaqachon ulangan![/green]")
            is_logged_in = True
            return

        qr_login = await client.qr_login()
        console.print("\n[bold green]📱 TeleGraph ilovangizni oching:[/bold green]")
        console.print("  [cyan]1.[/cyan] Sozlamalar (Settings) ga kiring")
        console.print("  [cyan]2.[/cyan] Qurilmalar (Devices) bo'limiga kiring")
        console.print("  [cyan]3.[/cyan] [bold]'Yangi qurilmani ulash' (Link Desktop Device)[/bold] tugmasini bosing")
        console.print("  [cyan]4.[/cyan] Quyidagi QR kodni telefon kamerasi bilan skaner qiling:\n")

        print_qr_code(qr_login.url)

        console.print("[dim]⏳ QR kod skaner qilinishi kutilmoqda...[/dim]")

        try:
            await qr_login.wait(timeout=120)
        except SessionPasswordNeededError:
            password = Prompt.ask("[yellow]🔐 Ushbu akkauntda 2FA (ikki bosqichli parol) o'rnatilgan. Parolni kiriting[/yellow]", password=True)
            await client.sign_in(password=password)

        me = await client.get_me()
        is_logged_in = True
        console.print(f"\n[bold green]🎉 Muvaffaqiyatli ulandi![/bold green]")
        console.print(f"👤 Ism: [cyan]{me.first_name}[/cyan] | Username: @{me.username or 'yo`q'} | ID: {me.id}")
        console.print(f"💾 Sessiya saqlandi: [dim]{session_file}.session[/dim]\n")
    except asyncio.TimeoutError:
        console.print("[bold red]❌ Vaqt tugadi. Qayta urinib ko'ring.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]❌ Xatolik yuz berdi: {str(e)}[/bold red]")
    finally:
        await client.disconnect()
        if not is_logged_in:
            cleanup_session_file(session_file)

async def login_with_phone():
    """Telefon raqam va SMS orqali ulash"""
    console.print("\n[bold cyan]📱 Telefon Raqam Orqali Ulash[/bold cyan]")
    phone = Prompt.ask("[yellow]Telefon raqamingizni to'liq kiriting[/yellow]", default="+998991234567").strip()
    if not phone:
        console.print("[red]Telefon raqam kiritilmadi![/red]")
        return

    clean_name = phone.replace("+", "").replace(" ", "").replace("-", "")
    session_file = SESSIONS_DIR / clean_name

    client = create_client(session_file)
    await client.connect()

    is_logged_in = False
    try:
        if await client.is_user_authorized():
            me = await client.get_me()
            console.print(f"[green]✅ Ushbu akkaunt ({me.first_name} | {phone}) allaqachon ulangan![/green]")
            is_logged_in = True
            return

        await client.send_code_request(phone)
        console.print(f"\n[bold green]📩 Tasdiqlash kodi TeleGraph ilovangizga yuborildi![/bold green]")
        code = Prompt.ask("[yellow]TeleGraph'ga kelgan 5 xonali kodni kiriting[/yellow]").strip()
        
        try:
            await client.sign_in(phone=phone, code=code)
        except SessionPasswordNeededError:
            password = Prompt.ask("[yellow]🔐 2FA parolini kiriting[/yellow]", password=True)
            await client.sign_in(password=password)

        me = await client.get_me()
        is_logged_in = True
        console.print(f"\n[bold green]🎉 Muvaffaqiyatli ulandi![/bold green]")
        console.print(f"👤 Ism: [cyan]{me.first_name}[/cyan] | ID: {me.id}")
        console.print(f"💾 Sessiya saqlandi: [dim]{session_file}.session[/dim]\n")
    except Exception as e:
        console.print(f"[bold red]❌ Xatolik: {str(e)}[/bold red]")
        console.print("[yellow]💡 Maslahat: QR kod orqali kirish usulidan foydalaning (1-menyu).[/yellow]")
    finally:
        await client.disconnect()
        if not is_logged_in:
            cleanup_session_file(session_file)

async def login_menu():
    console.print("\n[bold yellow]Akkaunt ulash usulini tanlang:[/bold yellow]")
    console.print("[green]1.[/green] 📷 [bold]QR Kod orqali[/bold] (Tavsiya etiladi — SMS yoki Captcha so'ramaydi)")
    console.print("[green]2.[/green] 📱 [bold]Telefon raqam orqali[/bold] (SMS/Tasdiqlash kodi bilan)")
    
    choice = Prompt.ask("[cyan]Tanlang[/cyan]", choices=["1", "2"], default="1")
    if choice == "1":
        await login_with_qr()
    else:
        await login_with_phone()

async def list_accounts():
    """Barcha saqlangan akkauntlar ro'yxatini va holatini chiqaradi"""
    session_files = list(SESSIONS_DIR.glob("*.session"))
    
    if not session_files:
        console.print("[yellow]⚠️ Hozircha hech qanday akkaunt ulanmagan.[/yellow]")
        return []

    table = Table(title="📱 Ulangan Telegram Akkauntlar", show_header=True, header_style="bold magenta")
    table.add_column("№", style="dim", width=4)
    table.add_column("Sessiya Nomi", style="cyan")
    table.add_column("Foydalanuvchi", style="green")
    table.add_column("Telefon/ID", style="yellow")
    table.add_column("Holati", style="bold")

    valid_sessions = []

    for idx, s_path in enumerate(session_files, 1):
        s_name = s_path.stem
        client = create_client(s_path)
        try:
            await client.connect()
            if await client.is_user_authorized():
                me = await client.get_me()
                user_str = f"{me.first_name or ''} {me.last_name or ''}".strip()
                if me.username:
                    user_str += f" (@{me.username})"
                phone_str = me.phone or str(me.id)
                status_str = "[green]Faol (Active) ✅[/green]"
                valid_sessions.append(s_path)
            else:
                user_str = "Noma'lum"
                phone_str = "-"
                status_str = "[red]Sessiya eskirgan ❌[/red]"
            await client.disconnect()
        except Exception:
            user_str = "Xatolik"
            phone_str = "-"
            status_str = "[red]Ulanib bo'lmadi ❌[/red]"
            if client.is_connected():
                await client.disconnect()

        table.add_row(str(idx), s_name, user_str, phone_str, status_str)

    console.print(table)
    return valid_sessions
