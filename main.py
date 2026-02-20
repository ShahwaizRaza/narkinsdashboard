from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time
import threading
import json
import os
from datetime import datetime, date

app = Flask(__name__)
CORS(app)

# ─── API Credentials ────────────────────────────────────────────────────────
HEADERS = {
    "accept": "*/*",
    "X-Api-Key": "4fbf65204fd440599dd3817b45cd869a",
    "X-Api-Secret": "bjHFJT6TbFz2egCjuffpMtnjCizckbYyAZmYKUyVFhMjARRhE8F4c67ATF72ddGgeb8f6wjQoSTqZuuGLv6dvhjqzPtwjfWAv25H",
    "X-App-Id": "4BC9199C-5C12-420A-8279-01B1C57CCE5D",
    "Content-Type": "application/json-patch+json"
}

REPORTS = {
    "ProductDateWiseSale": {
        "url": "https://narkins.splendidaccounts.com/api/narkins-textile-industries/2125/Reports/ProductDateWiseSaleReport",
        # Fixed: removed duplicate 25762
        "branchIds": [2248, 2249, 5574, 5701, 7965, 13468, 13469, 21578,
                      24709, 24710, 24711, 25762, 2994, 23405, 12721,
                      26777, 26778, 26779, 26780, 26781]
    }
}

CACHE_DURATION   = 300   # seconds before a background refresh is triggered
DISK_CACHE_FILE  = "narkins_cache.json"   # survives server restarts

# ─── In-memory store ─────────────────────────────────────────────────────────
# Structure: { report_type: {"data": [...], "fetched_at": iso_str, "cache_date": date_str} }
data_cache: dict = {}
_refresh_lock = threading.Lock()   # prevents simultaneous fetches


# ─── Disk Cache ──────────────────────────────────────────────────────────────
def save_to_disk(report_type: str, records: list):
    """Persist cache to disk so a server restart doesn't cold-start."""
    try:
        existing = {}
        if os.path.exists(DISK_CACHE_FILE):
            with open(DISK_CACHE_FILE, "r") as f:
                existing = json.load(f)
        existing[report_type] = {
            "data": records,
            "fetched_at": datetime.now().isoformat(),
            "cache_date": str(date.today())
        }
        with open(DISK_CACHE_FILE, "w") as f:
            json.dump(existing, f)
        print(f"💾 Disk cache updated ({len(records)} records)")
    except Exception as e:
        print(f"⚠️  Disk cache write failed: {e}")


def load_from_disk() -> dict:
    """Load persisted cache on startup."""
    if not os.path.exists(DISK_CACHE_FILE):
        return {}
    try:
        with open(DISK_CACHE_FILE, "r") as f:
            raw = json.load(f)
        result = {}
        for rt, entry in raw.items():
            result[rt] = {
                "data":       entry["data"],
                "fetched_at": datetime.fromisoformat(entry["fetched_at"]),
                "cache_date": entry["cache_date"]
            }
        print(f"📂 Loaded disk cache: {', '.join(f'{k}={len(v[\"data\"])} records' for k, v in result.items())}")
        return result
    except Exception as e:
        print(f"⚠️  Disk cache read failed: {e}")
        return {}


# ─── Core Fetch ──────────────────────────────────────────────────────────────
def _do_fetch(report_type: str) -> list | None:
    """
    Raw API call with retries. Returns processed list or None on failure.
    Does NOT touch the cache — callers handle that.
    """
    config = REPORTS[report_type]
    today  = date.today()
    first  = today.replace(day=1)

    payload = {
        "fromDate":  first.strftime("%Y-%m-%d"),
        "endDate":   today.strftime("%Y-%m-%d"),
        "branchIds": config["branchIds"],
        "ascending": True,
        "orderBy":   "Date"
    }

    for attempt in range(3):
        try:
            print(f"  🔄 Attempt {attempt + 1}/3  ({first} → {today})")
            resp = requests.post(config["url"], headers=HEADERS,
                                 json=payload, timeout=30)

            if resp.status_code == 200:
                raw = resp.json()
                if isinstance(raw, list) and raw:
                    records = [
                        {
                            "Date":         item.get("date", ""),
                            "Month":        item.get("monthName", ""),
                            "Branch":       item.get("branchName", ""),
                            "Code":         item.get("productCode", ""),
                            "Product Name": item.get("productName", ""),
                            "Category":     item.get("productCategoryName", ""),
                            "SOLD QTY":     item.get("soldQuantity", 0),
                            "Type":         item.get("symbol", ""),
                            "Total Sales":  item.get("includingTaxAmount", 0)
                        }
                        for item in raw
                    ]
                    print(f"  ✅ Fetched {len(records)} records")
                    return records
                print("  ⚠️  API returned empty list")
                return []

            print(f"  ❌ HTTP {resp.status_code}: {resp.text[:200]}")

        except requests.exceptions.Timeout:
            print(f"  ⏱️  Timeout on attempt {attempt + 1}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Request error: {e}")
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            return None

        if attempt < 2:
            time.sleep(2)

    print("  ❌ All 3 attempts failed")
    return None


def _update_cache(report_type: str, records: list):
    """Write new data into memory and disk caches."""
    data_cache[report_type] = {
        "data":       records,
        "fetched_at": datetime.now(),
        "cache_date": str(date.today())
    }
    save_to_disk(report_type, records)


def fetch_api_data(report_type: str) -> list | None:
    """
    Public entry point. Fetches, updates both caches, returns records.
    Thread-safe — won't fire two simultaneous fetches for the same report.
    """
    if report_type not in REPORTS:
        return None
    with _refresh_lock:
        print(f"\n{'='*50}")
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Fetching: {report_type}")
        records = _do_fetch(report_type)
        if records is not None:
            _update_cache(report_type, records)
        return records


# ─── Background Refresh Thread ───────────────────────────────────────────────
def _background_refresher():
    """
    Runs forever in a daemon thread.
    Wakes every 60 s and refreshes any cache that is stale or from yesterday.
    Users NEVER wait — they always get the last good data instantly.
    """
    print("🔁 Background refresher started")
    while True:
        time.sleep(60)
        now  = datetime.now()
        today_str = str(date.today())

        for rt in list(REPORTS.keys()):
            entry = data_cache.get(rt)
            if entry is None:
                continue  # will be fetched on first request
            age = (now - entry["fetched_at"]).total_seconds()
            is_stale    = age >= CACHE_DURATION
            is_old_day  = entry["cache_date"] != today_str

            if is_stale or is_old_day:
                reason = "new day" if is_old_day else f"stale ({int(age)}s)"
                print(f"🔁 Background refresh [{reason}]: {rt}")
                fetch_api_data(rt)


# ─── Routes ──────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return jsonify({
        "status": "running",
        "message": "Narkins API is running!",
        "endpoints": {
            "/api/data":         "GET  ?reportType=ProductDateWiseSale",
            "/api/refresh":      "POST ?reportType=ProductDateWiseSale",
            "/api/cache-status": "GET"
        },
        "cache_duration_seconds": CACHE_DURATION
    })


@app.route("/api/data", methods=["GET"])
def get_data():
    """
    Returns cached data immediately.
    If cache is empty (very first start, no disk cache) fetches synchronously.
    Otherwise the background thread keeps cache fresh — zero wait for users.
    """
    report_type = request.args.get("reportType", "ProductDateWiseSale")
    if report_type not in REPORTS:
        return jsonify({"error": "Invalid report type"}), 400

    entry = data_cache.get(report_type)

    if entry is None:
        # Cold start with no disk cache — must fetch synchronously once
        print(f"🆕 Cold start fetch for {report_type}")
        records = fetch_api_data(report_type)
        if records is None:
            return jsonify({"error": "Failed to fetch data"}), 500
        return jsonify(records)

    age = int((datetime.now() - entry["fetched_at"]).total_seconds())
    print(f"📦 Serving cache ({age}s old, {len(entry['data'])} records)")
    return jsonify(entry["data"])


@app.route("/api/refresh", methods=["POST"])
def refresh_data():
    """Force-refresh on demand (e.g. from Streamlit's Refresh button)."""
    report_type = request.args.get("reportType", "ProductDateWiseSale")
    if report_type not in REPORTS:
        return jsonify({"error": "Invalid report type"}), 400

    print(f"🔄 Manual refresh: {report_type}")
    records = fetch_api_data(report_type)

    if records is not None:
        return jsonify({
            "status":  "success",
            "records": len(records),
            "date":    str(date.today())
        })
    return jsonify({"status": "error", "message": "Fetch failed"}), 500


@app.route("/api/cache-status", methods=["GET"])
def cache_status():
    now = datetime.now()
    status = {}
    for rt, entry in data_cache.items():
        age = int((now - entry["fetched_at"]).total_seconds())
        status[rt] = {
            "cached_date":  entry["cache_date"],
            "cache_time":   entry["fetched_at"].strftime("%Y-%m-%d %H:%M:%S"),
            "age_seconds":  age,
            "age_minutes":  round(age / 60, 1),
            "records":      len(entry["data"]),
            "is_fresh":     age < CACHE_DURATION,
            "is_today":     entry["cache_date"] == str(date.today())
        }
    return jsonify({
        "current_time":           now.strftime("%Y-%m-%d %H:%M:%S"),
        "cache_duration_seconds": CACHE_DURATION,
        "caches":                 status
    })


# ─── Startup ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════╗
║   🚀 NARKINS SALES API SERVER STARTING...    ║
╚═══════════════════════════════════════════════╝
""")
    # 1. Try loading from disk first (instant — no API call)
    disk = load_from_disk()
    today_str = str(date.today())
    for rt, entry in disk.items():
        data_cache[rt] = entry
        print(f"📂 Restored {len(entry['data'])} records for {rt} from disk")

    # 2. For any report still missing or from a previous day, fetch now
    for rt in REPORTS:
        entry = data_cache.get(rt)
        if entry is None or entry["cache_date"] != today_str:
            print(f"📊 Fetching fresh data for {rt}...")
            fetch_api_data(rt)

    # 3. Start background refresher
    t = threading.Thread(target=_background_refresher, daemon=True)
    t.start()

    print(f"\n{'='*50}")
    print("✅ Server ready at http://127.0.0.1:5000")
    print(f"{'='*50}\n")

    app.run(debug=False, port=5000, use_reloader=False)
