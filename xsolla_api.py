import asyncio
import json
import random
import urllib.parse
import httpx
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from answers_manager import AnswersManager

console = Console(force_terminal=True, legacy_windows=False)

class XsollaRewardsAPI:
    """
    Xsolla Rewards Backend API mijozi (prod.xsollapi.com).
    - initData yoki havola berilsa: x-tokenni o'zi avtomatik generatsiya qilib oladi.
    - x-token berilsa: to'g'ridan-to'g'ri ishlaydi.
    - Daily Check-in, Daily/Weekly Rewards, Homescreen, Recap, Giveaways va Quiz'larni to'liq avtomatlashtiradi.
    """
    def __init__(self, token_or_data: str, session_name: str, proxy: Optional[dict] = None):
        self.raw_input = token_or_data.strip()
        self.session_name = session_name
        self.proxy = proxy
        self.base_url = "https://prod.xsollapi.com/api"
        self.project_id = "282076"
        self.token: Optional[str] = None
        self.user_data: Dict[str, Any] = {}
        
        # Agar to'g'ridan-to'g'ri x-token berilgan bo'lsa
        if len(self.raw_input) in [37, 36, 32, 40] and not any(x in self.raw_input for x in ["=", "&", "http", "user"]):
            self.token = self.raw_input

    def _extract_init_data(self) -> str:
        """Kiritilgan har qanday havoladan initData ni ajratib oladi va tozalaydi"""
        raw = self.raw_input
        init_part = raw
        if "#tgWebAppData=" in raw:
            init_part = raw.split("#tgWebAppData=")[1].split("&tgWebAppVersion")[0]
        elif "?tgWebAppData=" in raw:
            init_part = raw.split("?tgWebAppData=")[1].split("&tgWebAppVersion")[0]
        elif "tgWebAppData=" in raw:
            init_part = raw.split("tgWebAppData=")[1].split("&")[0]

        # Kerak bo'lsa bir yoki ikki marta unquote qilish
        unquoted = urllib.parse.unquote(init_part)
        if "%26" in unquoted or "%3D" in unquoted or "%25" in unquoted:
            unquoted = urllib.parse.unquote(unquoted)
            
        return unquoted

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.107 Mobile Safari/537.36 Telegram-Android/11.5.3 (Samsung SM-G998B; Android 14; SDK 34; armeabi-v7a)",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://webapp.xsollapi.com/",
            "Origin": "https://webapp.xsollapi.com",
            "x-project-id": self.project_id,
            "content-type": "application/json"
        }
        if self.token:
            headers["x-token"] = self.token
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        proxy_url = None
        if self.proxy:
            proxy_url = self.proxy.get("https") or self.proxy.get("http") or self.proxy.get("url")
        
        return httpx.AsyncClient(
            headers=self._get_headers(),
            proxy=proxy_url,
            timeout=25.0,
            follow_redirects=True
        )

    async def authenticate(self) -> bool:
        """
        Agar x-token bo'lmasa, initData orqali avtomatik x-token oladi.
        So'ngra profilni tekshiradi.
        """
        # 1. Agar token hali olinmagan bo'lsa (initData orqali avto-login)
        if not self.token:
            init_data = self._extract_init_data()
            payload = {
                "projectId": self.project_id,
                "telegramInfo": {
                    "private": init_data
                }
            }
            async with await self._get_client() as client:
                try:
                    auth_res = await client.post(f"{self.base_url}/auth/social/login", json=payload)
                    if auth_res.status_code == 200:
                        token_data = auth_res.json()
                        self.token = token_data.get("token")
                        console.print(f"[bold green]✓ [{self.session_name}] x-token avtomatik olindi: {self.token[:12]}...[/bold green]")
                    else:
                        console.print(f"[yellow]⚠️ Avto-token olishda xatolik ({self.session_name}): Status {auth_res.status_code}[/yellow]")
                        return False
                except Exception as e:
                    console.print(f"[red]❌ Avto-token so'rovida xatolik: {str(e)}[/red]")
                    return False

        # 2. Yangi token bilan yangi client orqali profilni olish
        async with await self._get_client() as client:
            try:
                res = await client.get(f"{self.base_url}/users/@me")
                if res.status_code == 200:
                    self.user_data = res.json()
                    return True
                else:
                    console.log(f"[yellow]⚠️ Auth javobi ({self.session_name}): Status {res.status_code}[/yellow]")
                    return False
            except Exception as e:
                console.log(f"[red]❌ Ulanishda xatolik ({self.session_name}): {str(e)}[/red]")
                return False

    async def get_profile(self) -> Dict[str, Any]:
        """Profil va yangilangan balansni oladi"""
        async with await self._get_client() as client:
            try:
                res = await client.get(f"{self.base_url}/users/@me")
                if res.status_code == 200:
                    self.user_data = res.json()
            except Exception:
                pass
            return self.user_data

    async def claim_daily_checkin(self) -> Dict[str, Any]:
        """Har kunlik Check-in bajarish"""
        async with await self._get_client() as client:
            try:
                res = await client.post(f"{self.base_url}/users/@me/daily-check-in", json={})
                if res.status_code in [200, 201]:
                    return {"success": True, "message": "Daily Check-in muvaffaqiyatli bajarildi!"}
                elif res.status_code in [400, 422]:
                    return {"success": False, "message": "Bugun allaqachon bajarilgan"}
            except Exception as e:
                return {"success": False, "message": str(e)}
            return {"success": False, "message": "Check-in tekshirildi"}

    async def claim_daily_reward(self) -> Dict[str, Any]:
        """Kunlik Daily Reward bonusini claim qilish"""
        async with await self._get_client() as client:
            try:
                res = await client.post(f"{self.base_url}/users/@me/daily-reward/claim", json={})
                if res.status_code in [200, 201]:
                    return {"success": True, "message": "Daily Reward olindi!"}
                elif res.status_code in [400, 422]:
                    return {"success": False, "message": "Bugun allaqachon olingan"}
            except Exception as e:
                return {"success": False, "message": str(e)}
            return {"success": False, "message": "Daily reward tekshirildi"}

    async def claim_weekly_reward(self) -> Dict[str, Any]:
        """Haftalik Weekly Reward bonusini claim qilish"""
        async with await self._get_client() as client:
            try:
                res = await client.post(f"{self.base_url}/users/@me/weekly-reward/claim", json={})
                if res.status_code in [200, 201]:
                    return {"success": True, "message": "Weekly Reward olindi!"}
            except Exception:
                pass
            return {"success": False, "message": "Weekly reward tekshirildi"}

    async def claim_extra_daily_bonuses(self) -> int:
        """Qo'shimcha kunlik bonuslarni olish (Homescreen va Recap)"""
        claimed = 0
        async with await self._get_client() as client:
            try:
                res_h = await client.post(f"{self.base_url}/users/@me/miniapp-add-homescreen", json={})
                if res_h.status_code in [200, 201]:
                    console.print("[bold green]  🎁 Homescreen qo'shish bonusi olindi![/bold green]")
                    claimed += 1
            except Exception:
                pass

            try:
                res_r = await client.post(f"{self.base_url}/users/@me/share-recap", json={})
                if res_r.status_code in [200, 201]:
                    console.print("[bold green]  🎁 Share Recap bonusi olindi![/bold green]")
                    claimed += 1
            except Exception:
                pass

        return claimed

    async def auto_join_giveaways(self) -> int:
        """Barcha mavjud bepul Giveaway (yutuqli tanlovlar)ga avtomatik qo'shilish"""
        joined = 0
        async with await self._get_client() as client:
            try:
                res = await client.get(f"{self.base_url}/ads/giveaways")
                if res.status_code == 200:
                    giveaways = res.json()
                    if isinstance(giveaways, list):
                        for g in giveaways:
                            g_id = g.get("id")
                            g_title = g.get("title", f"Giveaway #{g_id}")
                            is_joined = g.get("joined", False)
                            if not is_joined and g_id:
                                try:
                                    j_res = await client.post(f"{self.base_url}/ads/giveaways/{g_id}/join", json={})
                                    if j_res.status_code in [200, 201]:
                                        console.print(f"[bold green]  🎉 Giveaway'ga muvaffaqiyatli qo'shildi: '{g_title}'[/bold green]")
                                        joined += 1
                                except Exception:
                                    pass
            except Exception:
                pass
        return joined

    async def claim_weekly_missions(self) -> int:
        """Haftalik topshiriqlardan yig'ilgan bonuslarni claim qilish"""
        claimed = 0
        async with await self._get_client() as client:
            try:
                res = await client.get(f"{self.base_url}/ads/weekly-offers")
                if res.status_code == 200:
                    data = res.json()
                    offers = data.get("offers", []) if isinstance(data, dict) else data
                    for off in offers:
                        m_type = off.get("type")
                        completed = off.get("completedCount", 0)
                        required = off.get("count", 1)
                        if completed >= required and m_type:
                            try:
                                c_res = await client.post(f"{self.base_url}/ads/weekly-offers/claim", json={"type": m_type})
                                if c_res.status_code in [200, 201]:
                                    console.print(f"[bold green]  💎 Haftalik vazifa mukofoti claim qilindi: {m_type}[/bold green]")
                                    claimed += 1
                            except Exception:
                                pass
            except Exception:
                pass
        return claimed

    async def get_active_offers(self) -> List[Dict[str, Any]]:
        """Barcha faol takliflar va viktorinalar ro'yxatini oladi"""
        has_premium = self.user_data.get("hasPremium", False) or self.user_data.get("subscription", {}).get("status") == "active"
        offers = []

        async with await self._get_client() as client:
            try:
                res = await client.get(f"{self.base_url}/ads/offers", params={"status": "active", "onlyMine": "false", "showInstallAppMissions": "true"})
                if res.status_code == 200:
                    raw_offers = res.json().get("offers", [])
                    for off in raw_offers:
                        off_id = off.get("id")
                        if off.get("premiumRequired") and not has_premium:
                            continue

                        det_res = await client.get(f"{self.base_url}/ads/offers/{off_id}")
                        if det_res.status_code == 200:
                            det = det_res.json()
                            if det.get("premiumRequired") and not has_premium:
                                continue
                            offers.append(det)
                        else:
                            offers.append(off)
            except Exception as e:
                console.log(f"[yellow]⚠️ Offers yuklashda: {str(e)}[/yellow]")
        return offers

    async def solve_quiz_in_offer(self, offer: Dict[str, Any]) -> bool:
        """Offer ichidagi Quiz (savol-javoblar)ni yechish"""
        offer_id = offer.get("id")
        offer_title = offer.get("title", f"Quiz #{offer_id}")
        quiz_data = offer.get("quiz", {})
        questions = quiz_data.get("questions", [])

        if not questions:
            return False

        console.print(f"\n[bold yellow]🧠 Viktorina: '{offer_title}' (Savollar soni: {len(questions)} ta)[/bold yellow]")

        answered_questions = []

        for q_idx, q in enumerate(questions, 1):
            q_id = q.get("id")
            q_text = q.get("question") or f"Savol #{q_idx}"
            options = q.get("options", [])

            if not options:
                continue

            chosen_option_id = None
            chosen_option_text = None

            # 1. Serverdan to'g'ri javobni olish (isValid=true ni tekshirish)
            for opt in options:
                if isinstance(opt, dict) and opt.get("isValid") is True:
                    chosen_option_id = opt.get("id")
                    chosen_option_text = opt.get("text", "")
                    console.print(f"[bold cyan]  ✓ [{q_idx}/{len(questions)}] Server to'g'ri javobni berdi: [yellow]'{chosen_option_text}'[/yellow][/bold cyan]")
                    AnswersManager.save_answer(q_text, chosen_option_text)
                    break

            # 2. Cache'dan topish (server isValid bermagan holda)
            if not chosen_option_id:
                cached_answer = AnswersManager.find_cached_answer(q_text)
                if cached_answer:
                    matched_id = AnswersManager.match_option(options, cached_answer)
                    if matched_id:
                        chosen_option_id = matched_id
                        chosen_option_text = cached_answer
                        console.print(f"[bold cyan]  ✓ [{q_idx}/{len(questions)}] Bazadan avtomatik belgilandi: [yellow]'{cached_answer}'[/yellow][/bold cyan]")

            # 3. Foydalanuvchidan so'rash (birinchi marta yangi savol)
            if not chosen_option_id:
                console.print("\n" + "="*55)
                console.print(Panel.fit(
                    f"[bold yellow]❓ SAVOL [{q_idx}/{len(questions)}]:[/bold yellow]\n\n"
                    f"[bold white]{q_text}[/bold white]\n\n" +
                    "\n".join([
                        f"  [cyan][{idx}][/cyan] {opt.get('text', opt) if isinstance(opt, dict) else str(opt)}"
                        for idx, opt in enumerate(options, 1)
                    ]),
                    title=f"Viktorina: {offer_title}",
                    border_style="yellow"
                ))

                choice_indices = [str(i) for i in range(1, len(options) + 1)]
                user_choice = Prompt.ask(
                    "[bold green]To'g'ri javob variantini tanlang[/bold green]",
                    choices=choice_indices,
                    default="1"
                )
                selected_opt = options[int(user_choice) - 1]
                chosen_option_id = selected_opt.get("id") if isinstance(selected_opt, dict) else selected_opt
                chosen_option_text = selected_opt.get("text") if isinstance(selected_opt, dict) else str(selected_opt)

                AnswersManager.save_answer(q_text, chosen_option_text)
                console.print(f"[bold green]💾 Javob bazaga saqlandi: '{chosen_option_text}'. Qolgan barcha akkauntlar bu savolni avtomatik yechadi![/bold green]\n")

            answered_questions.append({
                "id": q_id,
                "answers": [
                    {
                        "id": chosen_option_id,
                        "isValid": False
                    }
                ]
            })

        async with await self._get_client() as client:
            payload = {"questions": answered_questions}
            try:
                res = await client.post(f"{self.base_url}/ads/offers/{offer_id}/check-quiz", json=payload)
                if res.status_code in [200, 201]:
                    # Serverdan qaytgan to'g'ri javoblarni cache'ga saqlash
                    try:
                        resp_data = res.json()
                        resp_quiz = resp_data.get("quiz", {})
                        for rq in resp_quiz.get("questions", []):
                            rq_text = rq.get("question", "")
                            for ropt in rq.get("options", []):
                                if ropt.get("isValid") is True:
                                    AnswersManager.save_answer(rq_text, ropt.get("text", ""))
                    except Exception:
                        pass
                    console.print(f"[bold green]  🎉 Viktorina muvaffaqiyatli yechildi va ball berildi! ('{offer_title}')[/bold green]")
                    return True
                elif res.status_code == 400 and "already completed" in res.text.lower():
                    console.print(f"[bold green]  ✅ Bu viktorina allaqachon yechilgan va ball olingan! ('{offer_title}')[/bold green]")
                    return True
                else:
                    console.print(f"[yellow]⚠️ Quiz javobi ({offer_title}): Status {res.status_code} | {res.text[:120]}[/yellow]")
            except Exception as e:
                console.print(f"[red]❌ Quiz yuborishda xatolik: {str(e)}[/red]")
        return False

    async def complete_and_claim_offer(self, offer: Dict[str, Any]) -> bool:
        """Har qanday offer/vazifani turiga qarab bajarish"""
        offer_id = offer.get("id")
        title = offer.get("title", f"Offer #{offer_id}")
        conditions = offer.get("conditions", {})

        if conditions.get("solveQuiz") or "quiz" in offer:
            return await self.solve_quiz_in_offer(offer)

        async with await self._get_client() as client:
            try:
                if conditions.get("openURL"):
                    res = await client.post(f"{self.base_url}/ads/offers/{offer_id}/check-url-visit", json={})
                    if res.status_code in [200, 201]:
                        console.print(f"[green]  ✅ Saytga tashrif vazifasi bajarildi: '{title}'[/green]")
                        return True

                if conditions.get("subscribeTelegramChannel"):
                    res = await client.post(f"{self.base_url}/ads/offers/{offer_id}/check-telegram-subscription", json={})
                    if res.status_code in [200, 201]:
                        console.print(f"[green]  ✅ Telegram obuna vazifasi bajarildi: '{title}'[/green]")
                        return True

                if conditions.get("installApp"):
                    res = await client.post(f"{self.base_url}/ads/offers/{offer_id}/check-app-install", json={})
                    if res.status_code in [200, 201]:
                        console.print(f"[green]  ✅ Ilova o'rnatish vazifasi bajarildi: '{title}'[/green]")
                        return True

                if conditions.get("connectDiscord"):
                    res = await client.post(f"{self.base_url}/ads/offers/{offer_id}/check-discord-connect", json={})
                    if res.status_code in [200, 201]:
                        console.print(f"[green]  ✅ Discord ulash vazifasi bajarildi: '{title}'[/green]")
                        return True
            except Exception:
                pass
        return False
