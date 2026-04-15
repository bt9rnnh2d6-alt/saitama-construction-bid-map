"""
Supabase bids テーブル内の「埼玉県外の座標」を null 化するワンショットメンテナンススクリプト。

使い方:
  1. .env ファイルに SUPABASE_URL と SUPABASE_SERVICE_KEY を設定
  2. python cleanup_supabase_coords.py

動作内容:
  - bids テーブルから lat/lon のある全件を取得
  - 埼玉県の境界ボックスから外れる案件の lat/lon を null に更新
  - 影響件数を表示（ピン自体は消えず、地図表示から外れるだけ）
"""

import os
import sys
import io
import json
import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ .env に SUPABASE_URL と SUPABASE_SERVICE_KEY を設定してください")
    sys.exit(1)

# 埼玉県の境界ボックス（scraper.py と同値）
SAITAMA_BBOX = {
    "min_lat": 35.7473, "max_lat": 36.2836,
    "min_lon": 138.7107, "max_lon": 139.9003,
}

def in_saitama(lat, lon):
    if lat is None or lon is None:
        return False
    return (SAITAMA_BBOX["min_lat"] <= lat <= SAITAMA_BBOX["max_lat"]
            and SAITAMA_BBOX["min_lon"] <= lon <= SAITAMA_BBOX["max_lon"])

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

def fetch_all():
    """lat/lon のある案件を全件取得"""
    url = f"{SUPABASE_URL}/rest/v1/bids"
    params = {
        "select": "id,case_id,location,lat,lon",
        "lat": "not.is.null",
        "limit": "10000",
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def nullify(case_id):
    """指定 case_id の lat/lon を null に更新"""
    url = f"{SUPABASE_URL}/rest/v1/bids"
    params = {"case_id": f"eq.{case_id}"}
    payload = {"lat": None, "lon": None}
    r = requests.patch(url, headers=HEADERS, params=params,
                       data=json.dumps(payload), timeout=15)
    r.raise_for_status()

def main():
    print("=" * 55)
    print(" Supabase 座標クリーンアップ（埼玉県外を null 化）")
    print("=" * 55)

    rows = fetch_all()
    print(f"  取得: {len(rows)} 件（lat/lon 有り）")

    bad = [r for r in rows if not in_saitama(r.get("lat"), r.get("lon"))]
    print(f"  埼玉県外: {len(bad)} 件")

    if not bad:
        print("  ✓ クリーンアップ対象なし")
        return

    for i, row in enumerate(bad, 1):
        cid = row.get("case_id")
        loc = row.get("location") or ""
        print(f"  [{i}/{len(bad)}] case_id={cid} location={loc[:40]} "
              f"({row.get('lat'):.4f},{row.get('lon'):.4f}) → null")
        try:
            nullify(cid)
        except Exception as e:
            print(f"    ⚠ 更新失敗: {e}")

    print("\n  ✓ 完了")

if __name__ == "__main__":
    main()
