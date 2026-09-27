import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

LEETIFY_API_KEY = os.getenv("LEETIFY_API_KEY")
BASE_URL = "https://api-public.cs-prod.leetify.com"
STEAM64_BASE = 76561197960265728
USER_AGENT = "CS2StatsTracker/1.0"


class LeetifyError(Exception):
    """An upstream service failure that can be shown to the user."""


def _json_response(path, steam64_id, timeout):
    try:
        response = requests.get(
            f"{BASE_URL}{path}",
            params={"steam64_id": steam64_id},
            headers=_headers(),
            timeout=timeout,
        )
        if response.status_code == 404:
            return None
        if response.status_code == 429:
            raise LeetifyError("Leetify จำกัดคำขอชั่วคราว กรุณาลองใหม่ภายหลัง")
        if response.status_code in (401, 403):
            raise LeetifyError("Leetify ปฏิเสธคำขอ กรุณาตรวจสอบ API key หรือสิทธิ์ของโปรไฟล์")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as exc:
        raise LeetifyError("เชื่อมต่อ Leetify ไม่สำเร็จ กรุณาลองใหม่ภายหลัง") from exc
    except ValueError as exc:
        raise LeetifyError("Leetify ส่งข้อมูลที่อ่านไม่ได้") from exc


def _headers():
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if LEETIFY_API_KEY:
        headers["_leetify_key"] = LEETIFY_API_KEY
    return headers


def resolve_steam64(query: str):
    """แปลงข้อความค้นหาเป็น Steam64 ID (ตัวเลข 17 หลัก)"""
    if not query:
        return None

    q = query.strip()

    # Steam profile URL: steamcommunity.com/profiles/7656119...
    match = re.search(r"steamcommunity\.com/profiles/(\d{15,17})", q, re.I)
    if match:
        return match.group(1)

    # Steam vanity URL: steamcommunity.com/id/username
    match = re.search(r"steamcommunity\.com/id/([^/?#]+)", q, re.I)
    if match:
        return _resolve_vanity(match.group(1))

    # STEAM_0:0:12345678 format
    match = re.match(r"^STEAM_[0-9]:([01]):(\d+)$", q, re.I)
    if match:
        y, z = int(match.group(1)), int(match.group(2))
        return str(STEAM64_BASE + z * 2 + y)

    # [U:1:12345678] format
    match = re.match(r"^\[U:1:(\d+)\]$", q, re.I)
    if match:
        return str(STEAM64_BASE + int(match.group(1)))

    # Direct 17-digit Steam64 ID
    if q.isdigit() and len(q) == 17:
        return q

    # Short numeric ID (convert to Steam64)
    if q.isdigit() and 1 <= len(q) <= 10:
        return str(STEAM64_BASE + int(q))

    # Vanity name
    if re.match(r"^[A-Za-z0-9_\-]+$", q):
        return _resolve_vanity(q)

    return None


def _resolve_vanity(vanity: str):
    """แปลง Vanity URL เป็น Steam64 ID"""
    try:
        response = requests.get(
            f"https://steamcommunity.com/id/{vanity}/?xml=1",
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        match = re.search(r"<steamID64>(\d{15,17})</steamID64>", response.text)
        if match:
            return match.group(1)
    except requests.exceptions.RequestException:
        return None
    return None


def _skill_value(value):
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return 0


def _skill_bar(value):
    score = _skill_value(value)
    if abs(score) <= 1.5:
        return max(0, min(100, round(score * 100, 2)))
    return max(0, min(100, score))


def _normalize_player(data: dict):
    winrate = data.get("winrate", 0) or 0
    try:
        winrate = float(winrate)
    except (TypeError, ValueError):
        winrate = 0
    if winrate <= 1:
        winrate *= 100

    ranks = data.get("ranks") or {}
    rating = data.get("rating") or data.get("ratings") or {}

    return {
        "name": data.get("name", "N/A"),
        "steam64_id": data.get("steam64_id"),
        "totalMatches": data.get("total_matches", data.get("totalMatches", 0)),
        "winRate": round(winrate, 2),
        "ranks": {
            "premier": ranks.get("premier"),
            "faceit": ranks.get("faceit"),
        },
        "ratings": {
            "aim": _skill_value(rating.get("aim", 0)),
            "positioning": _skill_value(rating.get("positioning", 0)),
            "utility": _skill_value(rating.get("utility", 0)),
            "clutch": _skill_value(rating.get("clutch", 0)),
        },
        "skill_rows": [
            ("Aim", _skill_value(rating.get("aim", 0))),
            ("Positioning", _skill_value(rating.get("positioning", 0))),
            ("Utility", _skill_value(rating.get("utility", 0))),
            ("Clutch", _skill_value(rating.get("clutch", 0))),
        ],
        "rating_bars": {
            "aim": _skill_bar(rating.get("aim", 0)),
            "positioning": _skill_bar(rating.get("positioning", 0)),
            "utility": _skill_bar(rating.get("utility", 0)),
            "clutch": _skill_bar(rating.get("clutch", 0)),
        },
        "raw": data,
    }


def _normalize_match(match: dict, steam64_id: str):
    scores = match.get("team_scores") or match.get("score") or match.get("teamScores") or []
    if scores and isinstance(scores[0], dict):
        team_scores = [item.get("score", 0) for item in scores]
    else:
        team_scores = list(scores)[:2]

    won = None
    stats = match.get("stats") or []
    player_stats = next(
        (item for item in stats if str(item.get("steam64_id")) == str(steam64_id)),
        None,
    )
    if player_stats:
        won = (player_stats.get("rounds_won") or 0) > (player_stats.get("rounds_lost") or 0)
    elif match.get("outcome"):
        won = str(match.get("outcome")).lower() == "win"
    else:
        won = bool(match.get("won"))

    date_value = (
        match.get("finished_at")
        or match.get("startedAt")
        or match.get("started_at")
        or ""
    )

    return {
        "steam64_id": steam64_id,
        "mapName": match.get("map_name") or match.get("mapName") or "Unknown",
        "won": won,
        "teamScores": team_scores,
        "startedAt": str(date_value),
    }


def get_player_data(query: str):
    """ดึงข้อมูลผู้เล่นจาก Steam ID หรือ URL"""
    steam64_id = resolve_steam64(query)
    if not steam64_id:
        return None

    data = _json_response("/v3/profile", steam64_id, 20)
    if not isinstance(data, dict) or not data.get("name"):
        return None
    player = _normalize_player(data)
    player["steam64_id"] = steam64_id
    return player


def get_match_history(query: str, limit: int = 5):
    """ดึงประวัติแมตช์ล่าสุดของผู้เล่น"""
    steam64_id = resolve_steam64(query)
    if not steam64_id:
        return []

    data = _json_response("/v3/profile/matches", steam64_id, 30)
    matches = data.get("matches", []) if isinstance(data, dict) else data or []
    if not isinstance(matches, list):
        raise LeetifyError("Leetify ส่งข้อมูลแมตช์ในรูปแบบที่ไม่รองรับ")
    return [_normalize_match(match, steam64_id) for match in matches[:limit] if isinstance(match, dict)]
