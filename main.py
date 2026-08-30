import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from bot_runner import run_all_accounts
from telegraph_autoclicker import run_all_accounts_ldplayer, run_single_active_account

console = Console(force_terminal=True, legacy_windows=False)

def show_banner():
    console.print(Panel.fit(
        "[bold cyan]⚡ XSOLLA REWARDS 2-IN-1 AVTO-BOT (API + LDPLAYER) ⚡[/bold cyan]\n"
        "[bold green]134 ta akkaunt uchun 2 xil kuchli rejim:[/bold green]\n"
        "[cyan]1. API Rejim[/cyan] -> [dim]Emulyatorsiz, to'g'ridan-to'g'ri internet orqali (juda tez)[/dim]\n"
        "[yellow]2. LDPlayer Rejim[/yellow] -> [dim]LDPlayer Telegraph orqali ekranda ko'rib yechish[/dim]",
        border_style="green"
    ))

async def main_menu():
    while True:
        show_banner()
        console.print("[bold yellow]Boshqaruv menyusi:[/bold yellow]\n")
        console.print("[bold green]1.[/bold green] 🚀 [bold]API REJIM[/bold] — [green]Barcha 134 ta akkauntni avtomat yechish[/green] (Tavsiya qilinadi)")
        console.print("[bold cyan]2.[/bold cyan] 🧪 [bold]API REJIM[/bold] — [cyan]Bitta akkauntni sinash[/cyan] (test uchun)")
        console.print("[bold yellow]3.[/bold yellow] 📱 [bold]LDPLAYER REJIM[/bold] — [yellow]Barcha akkauntlarni LDPlayerda yechish[/yellow]")
        console.print("[bold magenta]4.[/bold magenta] 📱 [bold]LDPLAYER REJIM[/bold] — [magenta]Faqat bitta ochiq akkauntni yechish[/magenta]")
        console.print("[red]0.[/red] 🚪 Dasturdan chiqish\n")

        choice = Prompt.ask("[cyan]Tanlovingizni kiriting[/cyan]", choices=["1", "2", "3", "4", "0"], default="1")

        if choice == "1":
            start_raw = Prompt.ask("[yellow]Nechanchi akkauntdan boshlaymiz?[/yellow]", default="1")
            try:
                s_num = int(start_raw)
            except ValueError:
                s_num = 1
            await run_all_accounts(start_from=s_num)

        elif choice == "2":
            idx_raw = Prompt.ask("[yellow]Qaysi akkaunt (data.txt dagi tartib raqami)?[/yellow]", default="1")
            try:
                idx = int(idx_raw)
            except ValueError:
                idx = 1
            await run_all_accounts(start_from=idx, end_at=idx)

        elif choice == "3":
            total = Prompt.ask("[yellow]LDPlayerda nechta akkaunt bor?[/yellow]", default="4")
            start = Prompt.ask("[yellow]Nechanchi akkauntdan boshlaymiz?[/yellow]", default="1")
            try:
                t_num, s_num = int(total), int(start)
            except ValueError:
                t_num, s_num = 4, 1
            run_all_accounts_ldplayer(total_accs=t_num, start_from=s_num)

        elif choice == "4":
            run_single_active_account()

        elif choice == "0":
            console.print("[bold yellow]Dastur yakunlandi. Xayr![/bold yellow]")
            sys.exit(0)

        input("\nDavom etish uchun [Enter] tugmasini bosing...")
        console.clear()

if __name__ == "__main__":
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        console.print("\n[yellow]Dastur to'xtatildi.[/yellow]")
