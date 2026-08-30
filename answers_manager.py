import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

ANSWERS_FILE = Path(__file__).resolve().parent / "answers_cache.json"

def normalize_text(text: str) -> str:
    """Matnni qidirish uchun tozalash (kichik harflar, bo'shliqlar, е/ё birlashtirish)"""
    if not text:
        return ""
    # ё -> е (rus tilida ko'p hollarda ё o'rniga е ishlatiladi)
    cleaned = str(text).lower().replace('ё', 'е')
    # Belgilarni olib tashlash
    cleaned = re.sub(r'[^\w\s]', '', cleaned).strip()
    return " ".join(cleaned.split())

class AnswersManager:
    """
    Savol-javoblar bazasi.
    1. Birinchi marta foydalanuvchi tanlagan to'g'ri javob matnini saqlaydi.
    2. Tartib (savollar yoki variantlar ketma-ketligi) o'zgarib tushsa ham,
       savol matni va to'g'ri variant matni orqali 100% aniq topadi.
    """
    @staticmethod
    def _load_cache() -> Dict[str, Any]:
        if ANSWERS_FILE.exists():
            try:
                with open(ANSWERS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @staticmethod
    def _save_cache(data: Dict[str, Any]):
        try:
            with open(ANSWERS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def find_cached_answer(cls, question_text: str) -> Optional[str]:
        """Savol matni bo'yicha bazadan to'g'ri javob matnini topadi"""
        cache = cls._load_cache()
        q_norm = normalize_text(question_text)
        
        # 1. To'g'ridan-to'g'ri kalit
        if question_text in cache:
            return cache[question_text]

        # 2. Normallashtirilgan matn bo'yicha qidirish
        for key, val in cache.items():
            if normalize_text(key) == q_norm or q_norm in normalize_text(key) or normalize_text(key) in q_norm:
                return val

        return None

    @classmethod
    def save_answer(cls, question_text: str, correct_option_text_or_val: Any):
        """Yangi savol va uning to'g'ri javobini saqlaydi"""
        cache = cls._load_cache()
        cache[str(question_text).strip()] = str(correct_option_text_or_val).strip()
        cls._save_cache(cache)

    @classmethod
    def match_option(cls, options: List[Any], saved_answer: str) -> Optional[Any]:
        """
        Variantlar tartibi almashib qolgan bo'lsa ham,
        saqlangan to'g'ri javob matniga mos keladigan variantni topadi.
        """
        saved_norm = normalize_text(saved_answer)

        for opt in options:
            if isinstance(opt, dict):
                opt_text = opt.get("text") or opt.get("title") or opt.get("value") or opt.get("answer") or ""
                opt_id = opt.get("id") or opt.get("_id") or opt.get("value")
                if normalize_text(opt_text) == saved_norm or saved_norm in normalize_text(opt_text):
                    return opt_id if opt_id is not None else opt
            else:
                if normalize_text(str(opt)) == saved_norm or saved_norm in normalize_text(str(opt)):
                    return opt

        return None
