import sys
import os
import time
import json
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import asyncio
import random
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import (
    BASE_DIR,
    MIN_DELAY_BETWEEN_ACCOUNTS,
    MAX_DELAY_BETWEEN_ACCOUNTS,
    MIN_DELAY_BETWEEN_TASKS,
    MAX_DELAY_BETWEEN_TASKS,
    get_proxy_for_session
)
from xsolla_api import XsollaRewardsAPI

console = Console(force_terminal=True, legacy_windows=False)
DATA_FILE = BASE_DIR / "data.txt"

def parse_token_or_line(raw_line: str) -> Optional[str]:
    """Qatordan x-token, initData yoki WebApp havolasini tozalab oladi"""
    line = raw_line.strip()
    if not line or line.startswith("#"):
        return None

    if "x-token:" in line.lower():
        return line.split(":")[-1].strip().strip("'").strip('"')

    if "-H 'x-token:" in line or '-H "x-token:' in line:
        part = line.split("x-token:")[1].split("'")[0].split('"')[0]
        return part.strip()

    return line.strip().strip("'").strip('"')

def load_accounts() -> List[str]:
    """data.txt faylidan barcha akkauntlar tokenlari yoki havolalarini yuklaydi"""
    if not DATA_FILE.exists():
        return []
    
    accounts = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            cleaned = parse_token_or_line(line)
            if cleaned:
                accounts.append(cleaned)
    return accounts

def format_duration(seconds: float) -> str:
    """Saniyalarni qulay formatga (daq, soniya) aylantiradi"""
    secs = int(seconds)
    mins = secs // 60
    rem_secs = secs % 60
    hours = mins // 60
    rem_mins = mins % 60

    if hours > 0:
        return f"{hours} soat {rem_mins} daqiqa {rem_secs} soniya"
    elif mins > 0:
        return f"{mins} daqiqa {rem_secs} soniya"
    else:
        return f"{secs} soniya"

async def process_account_token(token_or_data: str, account_index: int, total_accounts: int, session_label: str = None):
    account_label = session_label if session_label else f"Akkaunt #{account_index}"
    console.print(f"\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
    console.print(f"[bold cyan]🚀 [{account_index}/{total_accounts}] Akkaunt boshlanmoqda: [yellow]{account_label}[/yellow][/bold cyan]")

    proxy = get_proxy_for_session(session_label or f"akk{account_index}")


    api = XsollaRewardsAPI(token_or_data=token_or_data, session_name=account_label, proxy=proxy)
    is_auth = await api.authenticate()

    if not is_auth:
        console.print(f"[bold red]❌ Akkaunt #{account_index}: Ulanib bo'lmadi yoki token eskirgan![/bold red]")
        return {"account": account_label, "status": "Xatolik ❌", "tasks_done": "-", "balance": "-", "level_exp": "-"}

    profile = api.user_data
    username = profile.get("username") or f"User #{profile.get('id', '')}"
    tg_info = profile.get("telegram", {})
    first_name = tg_info.get("firstName", "").strip()
    last_name = tg_info.get("lastName", "").strip()
    tg_user = tg_info.get("username", "").strip()

    name_parts = []
    if first_name or last_name:
        name_parts.append(f"{first_name} {last_name}".strip())
    if tg_user:
        name_parts.append(f"@{tg_user}")
    tg_name_str = " ".join(name_parts)

    init_balance = float(profile.get("balance", 0))
    streak = profile.get("currentStreak", 0)
    lvl_info = profile.get("level", {})
    cur_lvl = lvl_info.get("level", 1)
    init_exp = int(lvl_info.get("exp", 0))
    next_exp = lvl_info.get("expToNext", 0)

    console.print(f"[bold green]👤 Akkaunt Nomi: [bold yellow]{tg_name_str or 'Nomsiz'}[/bold yellow] | Login: [cyan]{username}[/cyan] | Streak: [yellow]{streak} kun[/yellow] | Boshlang'ich: [yellow]{init_balance} UC[/yellow] | [cyan]Lvl {cur_lvl} ({init_exp} EXP)[/cyan][/bold green]")

    # 2. Daily Check-in bajarish
    console.print("[yellow]📅 Kunlik Daily Check-in tekshirilmoqda...[/yellow]")
    checkin_res = await api.claim_daily_checkin()
    if checkin_res.get("success"):
        console.print(f"[bold green]🎁 {checkin_res.get('message')}[/bold green]")
    else:
        console.print(f"[dim]ℹ️ Daily Check-in: {checkin_res.get('message')}[/dim]")

    # 3. Daily Reward Claim
    console.print("[yellow]🎁 Daily Reward tekshirilmoqda...[/yellow]")
    daily_rew = await api.claim_daily_reward()
    if daily_rew.get("success"):
        console.print(f"[bold green]🎁 {daily_rew.get('message')}[/bold green]")
    else:
        console.print(f"[dim]ℹ️ Daily Reward: {daily_rew.get('message')}[/dim]")

    # 4. Weekly Reward Claim
    weekly_rew = await api.claim_weekly_reward()
    if weekly_rew.get("success"):
        console.print(f"[bold green]🎉 Weekly Reward muvaffaqiyatli olindi![/bold green]")

    # 5. Qo'shimcha kunlik bonuslar (Homescreen & Recap)
    await api.claim_extra_daily_bonuses()

    # 6. Bepul Giveaways (Yutuqli o'yinlar) ga avto-qo'shilish
    console.print("[yellow]🎁 Bepul Giveaway tanlovlari tekshirilmoqda...[/yellow]")
    await api.auto_join_giveaways()

    # 7. Viktorinalar va Takliflar (Offers / Quizzes)
    console.print("[yellow]📋 Faol Viktorinalar (Quiz) va Topshiriqlar tekshirilmoqda...[/yellow]")
    offers = await api.get_active_offers()
    completed_count = 0

    if offers:
        console.print(f"[cyan]Topilgan faol vazifalar va viktorinalar: {len(offers)} ta[/cyan]")
        for off in offers:
            off_id = off.get("id")
            task_delay = random.uniform(MIN_DELAY_BETWEEN_TASKS, MAX_DELAY_BETWEEN_TASKS)
            await asyncio.sleep(task_delay)

            success = await api.complete_and_claim_offer(off)
            if success:
                completed_count += 1
    else:
        console.print("[dim]Hozirda yangi vazifalar topilmadi.[/dim]")

    # 8. Haftalik topshiriqlar mukofotini claim qilish
    await api.claim_weekly_missions()

    # 9. Mukofot va balans hisoblanishini kutish va tasdiqlash (Verification loop)
    console.print("[dim]⏳ Balans va mukofotlar hisoblanishi kutilmoqda va tekshirilmoqda...[/dim]")
    
    poll_attempts = 6
    final_balance = init_balance
    final_exp = init_exp
    f_lvl = cur_lvl
    f_next = next_exp

    for attempt in range(poll_attempts):
        await asyncio.sleep(2.5)
        final_profile = await api.get_profile()
        final_balance = float(final_profile.get("balance", init_balance))
        f_lvl_info = final_profile.get("level", {})
        f_lvl = f_lvl_info.get("level", cur_lvl)
        final_exp = int(f_lvl_info.get("exp", init_exp))
        f_next = f_lvl_info.get("expToNext", next_exp)

        # Agar balans oshgan bo'lsa, kutishni to'xtatib darhol tasdiqlaymiz
        if final_balance > init_balance or final_exp > init_exp:
            break

    earned_uc = round(final_balance - init_balance, 2)
    earned_exp = final_exp - init_exp

    uc_gain_str = f" (+{earned_uc} UC)" if earned_uc > 0 else ""
    exp_gain_str = f" (+{earned_exp} EXP)" if earned_exp > 0 else ""

    console.print(f"[bold green]✨ Tasdiqlandi! Balans: [bold yellow]{final_balance} UC{uc_gain_str}[/bold yellow] | Daraja: [cyan]Level {f_lvl} ({final_exp} EXP{exp_gain_str}, keyingisiga {f_next} EXP)[/cyan][/bold green]")

    balance_display = f"{final_balance} UC" + (f" ([green]+{earned_uc}[/green])" if earned_uc > 0 else "")
    exp_display = f"Lvl {f_lvl} ({final_exp} EXP)" + (f" ([green]+{earned_exp}[/green])" if earned_exp > 0 else "")

    acc_display = f"{account_label} | {tg_name_str} ({username})" if tg_name_str else f"{account_label} ({username})"
    return {
        "account": acc_display,
        "status": "Muvaffaqiyatli ✅",
        "tasks_done": completed_count,
        "balance": balance_display,
        "level_exp": exp_display
    }

async def run_all_accounts(start_from: int = 1, end_at: int = None):
    """Barcha akkauntlarni navbatma-navbat xavfsiz ishga tushiradi va umumiy vaqtni hisoblaydi"""
    accounts = load_accounts()
    
    if not accounts:
        console.print("\n[bold red]❌ data.txt faylida hech qanday akkaunt topilmadi![/bold red]")
        console.print("[yellow]Iltimos, data.txt fayliga x-token yoki WebApp havolasini joylang.[/yellow]\n")
        return

    start_index = max(1, min(start_from, len(accounts)))
    end_index = min(end_at if end_at else len(accounts), len(accounts))
    start_time = time.time()

    console.print(Panel.fit(
        f"[bold green]🤖 Xsolla Rewards Avtomatlashtirish Boshlandi[/bold green]\n"
        f"Boshlanish nuqtasi: [bold yellow]Akkaunt #{start_index}[/bold yellow] dan [bold cyan]#{end_index}[/bold cyan] gacha\n"
        f"[dim]Server: https://prod.xsollapi.com (100% Xavfsiz, LDPlayer kerak emas!)[/dim]",
        title="Xsolla Rewards Bot Runner",
        border_style="green"
    ))

    results = []

    for i in range(start_index, end_index + 1):
        try:
            token = accounts[i - 1]
            res = await process_account_token(token, i, end_index)
            results.append(res)
        except Exception as e:
            console.print(f"\n[bold red]❌ Akkaunt #{i} da xatolik: {str(e)}[/bold red]")
            results.append({
                "account": f"Akkaunt #{i}",
                "status": "Xatolik ❌",
                "tasks_done": "-",
                "balance": "-",
                "level_exp": "-"
            })

        if i < end_index:
            delay = random.uniform(MIN_DELAY_BETWEEN_ACCOUNTS, MAX_DELAY_BETWEEN_ACCOUNTS)
            console.print(f"\n[cyan]⏳ Keyingi akkauntgacha {int(delay)} soniya kutilmoqda (antiban delay)...[/cyan]")
            try:
                await asyncio.sleep(delay)
            except (asyncio.CancelledError, KeyboardInterrupt):
                console.print("[yellow]⚠️ To'xtatish so'rovi qabul qilindi. Hisobot chiqarilmoqda...[/yellow]")
                break

    total_elapsed = time.time() - start_time
    formatted_time = format_duration(total_elapsed)

    # Yakuniy hisobot jadvali
    console.print("\n")
    table = Table(title="📊 Barcha Akkauntlar Bo'yicha Yakuniy Hisobot", show_header=True, header_style="bold magenta")
    table.add_column("№", style="dim", width=4)
    table.add_column("Akkaunt / Ism", style="cyan")
    table.add_column("Holati", style="bold")
    table.add_column("Bajarilgan", style="green")
    table.add_column("Balans (UC)", style="yellow")
    table.add_column("Daraja / EXP", style="magenta")

    for idx, r in enumerate(results, 1):
        table.add_row(
            str(idx),
            r.get("account", "-"),
            r.get("status", "-"),
            str(r.get("tasks_done", "-")),
            str(r.get("balance", "-")),
            str(r.get("level_exp", "-"))
        )

    console.print(table)
    console.print(Panel.fit(
        f"[bold green]🎉 Barcha akkauntlar bo'yicha amallar yakunlandi![/bold green]\n"
        f"⏱️ Jami sarflangan umumiy vaqt: [bold yellow]{formatted_time}[/bold yellow]\n"
        f"📱 Ishlangan akkauntlar soni: [bold cyan]{len(accounts)} ta[/bold cyan]",
        title="✨ Jarayon Xulosasi",
        border_style="green"
    ))

if __name__ == "__main__":
    asyncio.run(run_all_accounts())


async def run_from_sessions(start_from: int = 1):
    """
    sessions/ papkasidagi .session fayllardan har biri uchun:
    1. Yangi Telegram WebApp havolasini avtomatik oladi
    2. Daily Check-in, Viktorina va barcha bonuslarni bajaradi
    Viktorinalarda ham +2 Orb 100% beriladi (haqiqiy Telegram sessiyasi orqali).
    """
    from webapp_auth import extract_init_data
    from config import SESSIONS_DIR

    session_files = sorted(SESSIONS_DIR.glob("*.session"))

    if not session_files:
        console.print("\n[bold red]❌ sessions/ papkasida hech qanday .session fayl topilmadi![/bold red]")
        console.print("[yellow]Avval akkauntlarni ulang: main.py → 7 (Telegram sessiya orqali ulash)[/yellow]\n")
        return

    total = len(session_files)
    start_index = max(1, min(start_from, total))
    start_time = time.time()

    console.print(Panel.fit(
        f"[bold green]🤖 SESSION Rejimi — Xsolla Rewards Avtomatlashtirish[/bold green]\n"
        f"Topilgan sessiya fayllari: [bold yellow]{total} ta[/bold yellow]\n"
        f"Boshlanish: [bold cyan]#{start_index}[/bold cyan] dan [bold cyan]#{total}[/bold cyan] gacha\n"
        f"[dim]Har bir akkauntda yangi Telegram WebApp havola avtomatik olinadi[/dim]\n"
        f"[bold green]✅ Viktorina Orblari ham to'liq beriladi![/bold green]",
        title="🔐 Telegram Session Runner",
        border_style="green"
    ))

    results = []

    for idx in range(start_index, total + 1):
        sess_path = session_files[idx - 1]
        sess_name = sess_path.stem

        console.print(f"\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print(f"[bold cyan]🔐 [{idx}/{total}] Session: [yellow]{sess_name}[/yellow][/bold cyan]")

        try:
            console.print(f"[dim]🌐 Yangi Telegram WebApp havolasi olinmoqda...[/dim]")
            init_data = await extract_init_data(sess_path)
            console.print(f"[bold green]✅ Yangi havola olindi![/bold green]")
        except Exception as e:
            console.print(f"[bold red]❌ Session '{sess_name}' dan havola olinmadi: {str(e)}[/bold red]")
            results.append({
                "account": sess_name,
                "status": "Session xatolik ❌",
                "tasks_done": "-",
                "balance": "-",
                "level_exp": "-"
            })
            if idx < total:
                await asyncio.sleep(5)
            continue

        proxy = get_proxy_for_session(sess_name)
        res = await process_account_token(init_data, idx, total, session_label=sess_name)
        results.append(res)

        if idx < total:
            delay = random.uniform(MIN_DELAY_BETWEEN_ACCOUNTS, MAX_DELAY_BETWEEN_ACCOUNTS)
            console.print(f"\n[cyan]⏳ Keyingi akkauntgacha {int(delay)} soniya kutilmoqda (antiban)...[/cyan]")
            await asyncio.sleep(delay)

    total_elapsed = time.time() - start_time
    formatted_time = format_duration(total_elapsed)

    console.print("\n")
    table = Table(title="📊 SESSION Rejim — Yakuniy Hisobot", show_header=True, header_style="bold magenta")
    table.add_column("№", style="dim", width=4)
    table.add_column("Sessiya / Akkaunt", style="cyan")
    table.add_column("Holati", style="bold")
    table.add_column("Bajarilgan", style="green")
    table.add_column("Balans (UC)", style="yellow")
    table.add_column("Daraja / EXP", style="magenta")

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            r.get("account", "-"),
            r.get("status", "-"),
            str(r.get("tasks_done", "-")),
            str(r.get("balance", "-")),
            str(r.get("level_exp", "-"))
        )

    console.print(table)
    console.print(Panel.fit(
        f"[bold green]🎉 Barcha sessiyalar bo'yicha amallar yakunlandi![/bold green]\n"
        f"⏱️ Jami sarflangan vaqt: [bold yellow]{formatted_time}[/bold yellow]\n"
        f"📱 Ishlangan sessiyalar: [bold cyan]{total} ta[/bold cyan]",
        title="✨ SESSION Jarayon Xulosasi",
        border_style="green"
    ))

