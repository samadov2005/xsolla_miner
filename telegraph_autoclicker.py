"""
LDPlayer Xsolla Rewards Auto-Bot (v4 - Precise Coordinates & Flow)
==================================================================
LDPlayer 960x540 Landscape rejimi.
100% ishonchli: No-Back strategiyasi (X va Chats orqali).
"""

import subprocess
import time
import os
import sys
import random
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel

console = Console(force_terminal=True, legacy_windows=False)

ADB_PATH = r"F:\program\LDPlayer\LDPlayer14\adb.exe"

def get_connected_device():
    res = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True, errors="ignore")
    lines = [l.strip() for l in res.stdout.splitlines() if "\tdevice" in l]
    if lines:
        return lines[0].split("\t")[0]
    subprocess.run([ADB_PATH, "connect", "127.0.0.1:5555"], capture_output=True)
    time.sleep(1)
    res2 = subprocess.run([ADB_PATH, "devices"], capture_output=True, text=True, errors="ignore")
    lines2 = [l.strip() for l in res2.stdout.splitlines() if "\tdevice" in l]
    if lines2:
        return lines2[0].split("\t")[0]
    return "127.0.0.1:5555"

DEVICE_ID = get_connected_device()

# ============================================================
# Aniq Tasdiqlangan Koordinatalar (960x540 Landscape)
# ============================================================
CHATS_TAB       = (356, 519)
SETTINGS_TAB    = (521, 519)
MANAGE_ACCS_BTN = (136, 431)
ACC_ROW_Y       = {1: 105, 2: 154, 3: 201, 4: 249}
ACC_ROW_X       = 95

# Chat & MiniApp
CHAT_OPEN_BTN   = (80, 508)      # Chat ichidagi "Открыть" / Open tugmasi
MINIAPP_X_CLOSE = (42, 46)       # MiniApp yuqori chapdagi "X Close"
MINIMIZED_CLOSE = (45, 520)      # Pastdagi minimized bar

# MiniApp Navigatsiya
NAV_HOME        = (96, 530)      # Pastki panel: Home
NAV_CHEST       = (336, 507)     # Chest (Daily chest)
QUESTS_TAB      = (253, 405)     # Quests bo'limi
GIVEAWAYS_TAB   = (709, 406)     # Giveaways bo'limi

# Viktorina
QUIZ_CARD_FREE  = (480, 447)     # Bepul viktorina kartasi
QUIZ_OPT_1      = (300, 235)     # 1-variant
QUIZ_OPT_2      = (300, 282)     # 2-variant (odatda to'g'ri)
QUIZ_OPT_3      = (300, 329)     # 3-variant
QUIZ_OPT_4      = (300, 376)     # 4-variant
QUIZ_FINISH_BTN = (480, 502)     # Finish / Next
QUIZ_CLAIM_BTN  = (480, 499)     # Claim reward
# ============================================================

def adb(*args):
    cmd = [ADB_PATH, "-s", DEVICE_ID] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, errors="ignore")

def tap(x, y, delay=1.0):
    adb("shell", "input", "tap", str(x), str(y))
    if delay > 0:
        time.sleep(delay)

def swipe(x1, y1, x2, y2, ms=400, delay=1.2):
    adb("shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(ms))
    if delay > 0:
        time.sleep(delay)

def ensure_connected():
    global DEVICE_ID
    DEVICE_ID = get_connected_device()
    return True

def go_to_chats():
    """Telegraph asosiy Chatlar tabiga qaytish"""
    tap(*CHATS_TAB, delay=1.2)

def close_miniapp():
    """MiniAppni X orqali yopish"""
    tap(*MINIAPP_X_CLOSE, delay=1.0)
    tap(*MINIMIZED_CLOSE, delay=0.5)

def switch_account(acc_num: int) -> bool:
    """Akkauntni almashtirish"""
    console.print(f"  [yellow]🔄 Akkaunt #{acc_num} ga o'tilmoqda...[/yellow]")
    go_to_chats()
    tap(*SETTINGS_TAB, delay=1.5)
    tap(*MANAGE_ACCS_BTN, delay=1.5)

    y_pos = ACC_ROW_Y.get(acc_num, 105)
    tap(ACC_ROW_X, y_pos, delay=1.5)

    # Open / Kirish
    tap(921, 321, delay=2.0)
    console.print(f"  [green]✅ Akkaunt #{acc_num} ga o'tildi![/green]")
    return True

def open_miniapp() -> bool:
    """MiniAppni ochish"""
    console.print("  [cyan]🌐 Xsolla Rewards MiniApp ochilmoqda...[/cyan]")
    go_to_chats()
    tap(*MINIMIZED_CLOSE, delay=0.5)

    # Chatdagi "Открыть" tugmasi
    tap(*CHAT_OPEN_BTN, delay=1.5)

    # MiniApp yuklanishi (10 soniya)
    console.print("  [dim]⏳ MiniApp yuklanishi kutilmoqda (10s)...[/dim]")
    time.sleep(10)
    return True

def solve_and_claim_quizzes(opt_choice: int = 2):
    """MiniApp ichida kvestlarni yechish va Claim qilish"""
    console.print("  [yellow]📋 Kvestlar va Viktorinalar ochilmoqda...[/yellow]")

    # 1. Home tabiga o't
    tap(*NAV_HOME, delay=1.5)

    # 2. Daily chest / check-in
    tap(*NAV_CHEST, delay=1.5)

    # 3. Kvestlar ro'yxatiga pastga scroll
    swipe(480, 450, 480, 200, ms=400, delay=1.5)

    # 4. Quests tab
    tap(*QUESTS_TAB, delay=1.5)

    # 5. Viktorina kartasini bosish
    tap(*QUIZ_CARD_FREE, delay=2.5)

    # 6. Variant tanlash
    if opt_choice == 1:
        tap(*QUIZ_OPT_1, delay=1.0)
    elif opt_choice == 2:
        tap(*QUIZ_OPT_2, delay=1.0)
    elif opt_choice == 3:
        tap(*QUIZ_OPT_3, delay=1.0)
    else:
        tap(*QUIZ_OPT_4, delay=1.0)

    # 7. Finish
    tap(*QUIZ_FINISH_BTN, delay=2.5)

    # 8. Claim reward
    tap(*QUIZ_CLAIM_BTN, delay=2.0)

    console.print("  [bold green]✓ Viktorina yechildi va Claim bosildi![/bold green]")

def run_single_active_account(q_opt: int = 2):
    """Hozirgi akkauntda yechish"""
    ensure_connected()
    open_miniapp()
    solve_and_claim_quizzes(q_opt)
    close_miniapp()
    go_to_chats()

def run_all_accounts_ldplayer(total_accs: int = 4, start_from: int = 1, q_opt: int = 2):
    """Barcha akkauntlarni LDPlayerda ketma-ket yechish"""
    ensure_connected()
    console.print(Panel.fit(
        f"[bold green]🤖 LDPlayer Xsolla Auto-Bot v4[/bold green]\n"
        f"Akkauntlar: #{start_from} dan #{total_accs} gacha\n"
        f"[dim]Har bir akkaunt ochilib, MiniApp kvestlari yechiladi va Claim qilinadi[/dim]",
        border_style="green"
    ))

    for i in range(start_from, total_accs + 1):
        console.print(f"\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
        console.print(f"[bold cyan]📱 [{i}/{total_accs}] Akkaunt #{i} boshlanmoqda...[/bold cyan]")

        switch_account(i)
        open_miniapp()
        solve_and_claim_quizzes(q_opt)
        close_miniapp()
        go_to_chats()

        console.print(f"[bold green]✅ Akkaunt #{i} muvaffaqiyatli yakunlandi![/bold green]")

        if i < total_accs:
            time.sleep(random.randint(3, 5))

if __name__ == "__main__":
    run_single_active_account()
