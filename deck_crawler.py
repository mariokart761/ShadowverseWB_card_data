#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Shadowverse 牌組資訊擷取器（雙模式：URL / Deck Code）+ URL 前處理
- URL 模式：支援官網連結樣式 /<lang>/deck/detail/?hash=... 轉換為 API 樣式 /web/DeckBuilder/deckHashDetail?hash=...
- Deck Code 模式：POST 到 https://shadowverse-wb.com/web/DeckCode/getDeck，payload: {"deck_code": "XXXX"}
- 兩種模式輸出相同欄位結構

使用範例
--------
# URL（API樣式，記得整段加引號以避免 & 被殼層吃掉）
python deck_crawler_dual.py --url "https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=...&lang=cht"

# URL（官網樣式，會自動轉換）
python deck_crawler_dual.py --url "https://shadowverse-wb.com/cht/deck/detail/?hash=..."

# Deck Code（4 碼）
python deck_crawler_dual.py --deck-code Ab1C

# 指定 User-Agent、輸出檔案
python deck_crawler_dual.py --deck-code Ab1C --ua "Mozilla/5.0" -o deck.json
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

GET_DECK_ENDPOINT = "https://shadowverse-wb.com/web/DeckCode/getDeck"

# 需要輸出的欄位
NEEDED_FIELDS = [
    "total_red_ether",
    "num_follower",
    "num_spell",
    "num_amulet",
    "mana_curve",
    "battle_format",
    "class_id",
    "sub_class_id",
    "sort_card_id_list",
    "deck_card_num",
]

# 常見包裹層鍵名
CANDIDATE_ROOT_KEYS = ["data", "result", "deckDetail", "deck", "payload"]

def _first_non_none(*vals):
    for v in vals:
        if v is not None:
            return v
    return None

def _dig(obj: Dict[str, Any], key: str) -> Optional[Any]:
    """在可能的容器層中找 key；若頂層沒有，就往常見 root key 裡找一次。"""
    if key in obj:
        return obj[key]
    for rk in CANDIDATE_ROOT_KEYS:
        sub = obj.get(rk)
        if isinstance(sub, dict) and key in sub:
            return sub[key]
    return None

def format_deck_data(raw: Dict[str, Any]) -> Dict[str, Any]:
    """將原始 JSON 對齊成需要的欄位，缺值給預設。"""
    return {
        "total_red_ether": _first_non_none(_dig(raw, "total_red_ether"), 0),
        "num_follower":    _first_non_none(_dig(raw, "num_follower"), 0),
        "num_spell":       _first_non_none(_dig(raw, "num_spell"), 0),
        "num_amulet":      _first_non_none(_dig(raw, "num_amulet"), 0),
        "mana_curve":      _first_non_none(_dig(raw, "mana_curve"), {}),
        "battle_format":   _first_non_none(_dig(raw, "battle_format"), 2),
        "class_id":        _first_non_none(_dig(raw, "class_id"), 5),
        "sub_class_id":    _first_non_none(_dig(raw, "sub_class_id"), None),
        "sort_card_id_list": _first_non_none(_dig(raw, "sort_card_id_list"), []),
        "deck_card_num":   _first_non_none(_dig(raw, "deck_card_num"), {}),
    }

def _decode_json_bytes(data: bytes) -> Dict[str, Any]:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        text = data.decode("latin-1", errors="replace")
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"內容不是合法 JSON：{e}") from e
    if not isinstance(obj, dict):
        raise RuntimeError("最外層 JSON 不是物件（dict），不符合預期")
    return obj

def fetch_json_via_url(url: str, user_agent: Optional[str] = None) -> Dict[str, Any]:
    headers = {}
    if user_agent:
        headers["User-Agent"] = user_agent
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
    except HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} - {e.reason}") from e
    except URLError as e:
        raise RuntimeError(f"URL 錯誤：{e.reason}") from e
    return _decode_json_bytes(data)

def fetch_json_via_deck_code(deck_code: str, user_agent: Optional[str] = None) -> Dict[str, Any]:
    """POST 到官方 getDeck 端點，payload: {\"deck_code\": \"XXXX\"}"""
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if user_agent:
        headers["User-Agent"] = user_agent
    body = json.dumps({"deck_code": deck_code}).encode("utf-8")
    req = Request(GET_DECK_ENDPOINT, headers=headers, data=body, method="POST")
    try:
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
    except HTTPError as e:
        # 盡量帶出伺服器回覆
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        msg = f"HTTP {e.code} - {e.reason}"
        if detail:
            msg += f" - {detail}"
        raise RuntimeError(msg) from e
    except URLError as e:
        raise RuntimeError(f"URL 錯誤：{e.reason}") from e
    return _decode_json_bytes(data)

def normalize_deck_url_if_needed(raw_url: str) -> Tuple[str, Optional[str]]:
    """
    若為舊樣式 https://shadowverse-wb.com/<lang>/deck/detail/?hash=... ，
    轉為 https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=... ，
    並回傳偵測到的 lang（若有）。
    回傳: (normalized_url, detected_lang or None)
    """
    u = urlparse(raw_url)
    path = (u.path or "").lower()
    host = (u.netloc or "").lower()

    # 只處理 shadowverse-wb.com domain
    if not host.endswith("shadowverse-wb.com"):
        return raw_url, None

    # 解析 query 以取得 hash
    q = dict(parse_qsl(u.query, keep_blank_values=True))
    hash_val = q.get("hash")

    # path segments（去掉空片段）
    segs = [s for s in path.split("/") if s]

    # 型態一：/<lang>/deck/detail[/]
    # 例如 /cht/deck/detail/
    detected_lang: Optional[str] = None
    if len(segs) >= 3 and segs[1] == "deck" and segs[2].startswith("detail"):
        # 第一段視為語言（排除 web 等非語言片段）
        first = segs[0]
        if first not in {"web", "deck", "builder"}:
            detected_lang = first

    # 型態二：/deck/detail[/]（不含語言片段）
    if detected_lang is None and len(segs) >= 2 and segs[0] == "deck" and segs[1].startswith("detail"):
        detected_lang = None  # 沒偵測到語言，但仍可能要轉換

    # 若命中上述其中一種、且有 hash，就轉換
    if (detected_lang is not None or (len(segs) >= 2 and segs[0] == "deck" and segs[1].startswith("detail"))) and hash_val:
        new_path = "/web/DeckBuilder/deckHashDetail"
        new_query_pairs = {"hash": hash_val}
        # 若原本 query 就帶 lang，沿用；否則帶上 path 偵測到的語言
        if "lang" in q:
            new_query_pairs["lang"] = q["lang"]
        elif detected_lang:
            new_query_pairs["lang"] = detected_lang
        new_u = urlunparse((u.scheme or "https", u.netloc, new_path, "", urlencode(new_query_pairs), ""))
        return new_u, detected_lang

    # 否則不變
    return raw_url, None

def add_or_update_lang_query(url: str, lang: Optional[str]) -> str:
    if not lang:
        return url
    u = urlparse(url)
    q = dict(parse_qsl(u.query, keep_blank_values=True))
    q["lang"] = lang
    new_query = urlencode(q)
    return urlunparse((u.scheme, u.netloc, u.path, u.params, new_query, u.fragment))

def scrape_deck_by_url(url: str, user_agent: Optional[str] = None) -> Dict[str, Any]:
    raw = fetch_json_via_url(url, user_agent=user_agent)
    return format_deck_data(raw)

def scrape_deck_by_code(deck_code: str, user_agent: Optional[str] = None) -> Dict[str, Any]:
    raw = fetch_json_via_deck_code(deck_code, user_agent=user_agent)
    return format_deck_data(raw)

def main():
    parser = argparse.ArgumentParser(description="Shadowverse 牌組資訊（URL / Deck Code 雙模式，含 URL 前處理）")
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="直接取用 JSON 的 URL（建議整段加引號）")
    g.add_argument("--deck-code", help="牌組代碼（4 碼）")
    parser.add_argument("--lang", help="（URL 模式可選）語言代碼，例如 cht/jpn；會覆蓋前處理所偵測到的語言")
    parser.add_argument("--ua", "--user-agent", dest="ua", default="Mozilla/5.0",
                        help="自訂 User-Agent（可選）")
    parser.add_argument("-o", "--output", help="輸出檔名（預設印到 stdout）")
    args = parser.parse_args()

    try:
        if args.url:
            # 先做舊樣式轉換（可偵測到 path 的語言）
            normalized_url, detected_lang = normalize_deck_url_if_needed(args.url)
            # 再以 --lang 覆蓋（若提供）
            fetch_url = add_or_update_lang_query(normalized_url, args.lang or detected_lang)
            deck = scrape_deck_by_url(fetch_url, user_agent=args.ua)
        else:
            deck_code = args.deck_code.strip()
            deck = scrape_deck_by_code(deck_code, user_agent=args.ua)
    except Exception as e:
        print(f"[錯誤] {e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(deck, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(deck, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
