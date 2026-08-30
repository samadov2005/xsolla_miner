import time
import asyncio
import schedule
from rich.console import Console
from bot_runner import run_all_accounts
from config import AUTO_RUN_TIME

console = Console()

def job():
    console.print(f"\n[bold green]⏰ Belgilangan vaqt yetib keldi ({AUTO_RUN_TIME}). Avtomatik ish boshlanmoqda...[/bold green]")
    asyncio.run(run_all_accounts())

def start_scheduler():
    console.print(f"[bold cyan]⏳ Har kunlik avtomatik reja (Scheduler) ishga tushdi![/bold cyan]")
    console.print(f"[yellow]Bot har kuni soat [bold]{AUTO_RUN_TIME}[/bold] da avtomatik barcha akkauntlarni aylantiradi.[/yellow]")
    console.print("[dim]To'xtatish uchun: Ctrl + C[/dim]\n")

    schedule.every().day.at(AUTO_RUN_TIME).do(job)

    # Birinchi marta darhol tekshirishni xohlaysizmi?
    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    start_scheduler()
