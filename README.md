# ⚡ Xsolla Rewards Multi-Account AI Auto-Bot

**@XsollaRewardsBot** MiniApp ilovasidagi kunlik vazifalar (**Daily Check-in**, **Viktorinalar / Quiz**, **Homescreen & Recap bonuslari**, **Giveawaylar**, **Haftalik kvestlar**)ni barcha akkauntlaringiz uchun 100% avtomatik yechish va mukofotlarni yig'ish dasturi.

---

## 🚀 Imkoniyatlar

- **🌐 1-Rejim: API Rejim (Ultra-tez)**
  - Emulyator talab qilmaydi, to'g'ridan-to'g'ri internet orqali ishlaydi.
  - 134+ ta akkauntni tezkor va barqaror yechib chiqadi.
  - Antiban xavfsiz kechikish (delay) tizimi.

- **📱 2-Rejim: LDPlayer Avtokliker Rejimi (v4)**
  - LDPlayer 960x540 planshet rejimida Telegraph orqali ekranda ko'rib yechadi.
  - No-Back xavfsiz navigatsiya tizimi (Telegraphdan chiqib ketmaydi).
  - Viktorina kartalarini ochib, javobni tanlaydi va "Claim reward" tugmasini bosadi.

- **🧠 Savol-Javoblar Bazasi (AI Answers Cache)**
  - Bir marta yechilgan har qanday savol javobi `answers_cache.json` ga saqlanadi.
  - Qolgan barcha 100+ akkauntlar savollarni avtomatik ravishda 100% to'g'ri yechadi.

---

## 📦 O'rnatish

1. Kerakli kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

2. `data.txt` fayliga o'z akkauntlaringizning WebApp havolalarini joylang:
```
https://webapp.xsollapi.com/#tgWebAppData=...
https://webapp.xsollapi.com/#tgWebAppData=...
```

---

## 🎮 Ishga tushirish

```bash
python main.py
```

Menyudan kerakli variantni tanlang:
- `1` — 🚀 **API Rejim**: Barcha 134 ta akkauntni avtomat yechish
- `2` — 🧪 **API Rejim**: Bitta akkauntni sinab ko'rish
- `3` — 📱 **LDPlayer Rejim**: Barcha akkauntlarni LDPlayerda ketma-ket yechish
- `4` — 📱 **LDPlayer Rejim**: Hozir ochiq turgan bitta akkauntda sinash
