from flask import Flask, request, jsonify, render_template
import urllib.request
import urllib.error
import json
import time

app = Flask(__name__)

WZ_API = "https://wzapi.vercel.app/get"
SERVERS = ["pk", "sg", "ind", "bd", "br", "vn", "th", "me", "tw", "us", "id", "ru", "cis", "na"]

_cache = {}
CACHE_TTL = 300


def wz_fetch(uid, server):
    url = f"{WZ_API}?uid={uid}&server={server}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Linux; Android 16) AppleWebKit/537.36 SHADOW-FF-Stats/1.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=18) as r:
            data = json.loads(r.read().decode())
        bi = data.get("basic_info") or {}
        if bi.get("nickname"):
            return data
        return None
    except Exception:
        return None


def normalize(data, detected_server):
    bi = data.get("basic_info", {})
    clan = data.get("clan_basic_info", {}) or {}
    social = data.get("social_info", {}) or {}
    return {
        "success": True,
        "server": detected_server,
        "nickname": bi.get("nickname", "?"),
        "uid": bi.get("account_id", ""),
        "level": bi.get("level", 0),
        "exp": bi.get("exp", 0),
        "likes": bi.get("liked", 0),
        "region": bi.get("region", detected_server.upper()),
        "br_rank": bi.get("rank", 0),
        "br_points": bi.get("ranking_points", 0),
        "br_max_rank": bi.get("max_rank", 0),
        "cs_rank": bi.get("cs_rank", 0),
        "cs_points": bi.get("cs_ranking_points", 0),
        "cs_max_rank": bi.get("cs_max_rank", 0),
        "clan_name": clan.get("clan_name", "") or bi.get("clan_name", ""),
        "clan_level": clan.get("clan_level", 0),
        "clan_members": clan.get("member_num", 0),
        "clan_capacity": clan.get("capacity", 0),
        "gender": (social.get("gender", "") or "").replace("Gender_", ""),
        "language": (social.get("language", "") or "").replace("Language_", ""),
        "created_at": bi.get("create_at", 0),
        "last_login": bi.get("last_login_at", 0),
        "banner_id": bi.get("banner_id", 0),
        "head_pic": bi.get("head_pic", 0),
        "badge_count": bi.get("badge_cnt", 0),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/player")
def player():
    uid = (request.args.get("uid") or "").strip()
    if not uid.isdigit() or len(uid) < 5 or len(uid) > 12:
        return jsonify({"success": False, "error": "INVALID_UID"}), 400

    now = time.time()
    if uid in _cache and now - _cache[uid]["ts"] < CACHE_TTL:
        d = dict(_cache[uid]["data"])
        d["cached"] = True
        return jsonify(d)

    for server in SERVERS:
        data = wz_fetch(uid, server)
        if data:
            out = normalize(data, server)
            _cache[uid] = {"ts": now, "data": out}
            return jsonify(out)

    return jsonify({"success": False, "error": "NOT_FOUND"}), 404


@app.route("/api/health")
def health():
    return jsonify({"ok": True})
