"""
Supabase アップロードスクリプト
=================================
scraper.py で生成された data/bids.js を読み込み、
Supabase の bids テーブルに upsert（同じ case_id なら上書き、なければ新規追加）する。

使い方:
  1. .env ファイルに SUPABASE_URL と SUPABASE_SERVICE_KEY を記載
  2. python push_to_supabase.py

依存:
  pip install requests python-dotenv
"""

import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os
import re
import json
import requests
from datetime import datetime

# --- 環境変数の読み込み（.env があれば使用）---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # GitHub Actions では環境変数が直接入るのでOK

SUPABASE_URL         = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BIDS_JS = os.path.join("data", "bids.js")


def load_bids_from_js(path):
    """data/bids.js からJSONを取り出す"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} が見つかりません。先に scraper.py を実行してください。")

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # const BID_DATA = [...]; の部分を抽出
    m = re.search(r"const\s+BID_DATA\s*=\s*(\[[\s\S]*?\]);", text)
    if not m:
        raise ValueError("bids.js から BID_DATA が取り出せません。")
    bids = json.loads(m.group(1))

    # メタ情報も取り出す
    m2 = re.search(r"const\s+BID_META\s*=\s*(\{[\s\S]*?\});", text)
    meta = json.loads(m2.group(1)) if m2 else {}

    return bids, meta


def upsert_bids(bids):
    """Supabase の bids テーブルに upsert"""
    url = f"{SUPABASE_URL}/rest/v1/bids"
    headers = {
        "apikey":        SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type":  "application/json",
        # on_conflict=case_id で重複時は更新
        "Prefer":        "resolution=merge-duplicates,return=minimal",
    }

    # case_id が空のものは除外（一意制約に引っかかる）
    valid = [b for b in bids if b.get("case_id")]
    skipped = len(bids) - len(valid)
    if skipped:
        print(f"  ⚠ case_id 空のため {skipped} 件スキップ")

    # 100件ずつ分割して送信
    CHUNK = 100
    total = 0
    for i in range(0, len(valid), CHUNK):
        chunk = valid[i:i + CHUNK]
        # updated_at を現在時刻に
        now_iso = datetime.utcnow().isoformat() + "Z"
        for b in chunk:
            b["updated_at"] = now_iso

        r = requests.post(
            url + "?on_conflict=case_id",
            headers=headers,
            data=json.dumps(chunk, ensure_ascii=False).encode("utf-8"),
            timeout=30,
        )
        if r.status_code not in (200, 201, 204):
            print(f"  ❌ 送信失敗 (HTTP {r.status_code})")
            print(f"     レスポンス: {r.text[:500]}")
            return total, False
        total += len(chunk)
        print(f"  ✓ {total}/{len(valid)} 件 送信済み")

    return total, True


def upsert_meta(meta):
    """meta テーブルに最終更新日時などを保存"""
    url = f"{SUPABASE_URL}/rest/v1/meta"
    headers = {
        "apikey":        SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates,return=minimal",
    }
    payload = [{
        "key":        "last_scrape",
        "value":      meta,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }]
    r = requests.post(
        url + "?on_conflict=key",
        headers=headers,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=15,
    )
    if r.status_code not in (200, 201, 204):
        print(f"  ⚠ meta 保存失敗 (HTTP {r.status_code}): {r.text[:200]}")
        return False
    return True


def main():
    print("=" * 55)
    print(" Supabase データ送信")
    print(f" {datetime.now():%Y/%m/%d %H:%M:%S}")
    print("=" * 55)

    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("\n❌ 環境変数が設定されていません。")
        print("   .env ファイルに以下を記載してください:")
        print("   SUPABASE_URL=https://xxxxx.supabase.co")
        print("   SUPABASE_SERVICE_KEY=sb_secret_xxxxx")
        return 1

    print(f"\n[1/3] {BIDS_JS} を読み込み中...")
    try:
        bids, meta = load_bids_from_js(BIDS_JS)
    except Exception as e:
        print(f"  ❌ {e}")
        return 1
    print(f"  ✓ {len(bids)} 件読み込み完了")

    print(f"\n[2/3] Supabase にアップロード中...")
    print(f"   URL: {SUPABASE_URL}")
    sent, ok = upsert_bids(bids)
    if not ok:
        print(f"\n❌ 失敗（{sent} 件まで送信済み）")
        return 1

    print(f"\n[3/3] メタ情報を保存...")
    if upsert_meta(meta):
        print(f"  ✓ 最終更新日時を保存")

    print(f"\n✅ 完了: {sent} 件を Supabase に送信しました。")
    return 0


if __name__ == "__main__":
    rc = main()
    if sys.platform == "win32":
        input("\nEnterキーを押して終了...")
    sys.exit(rc)
