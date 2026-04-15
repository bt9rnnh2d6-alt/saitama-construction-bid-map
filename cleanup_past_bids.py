"""
Supabase bids テーブルから、開札日（bid_date）が今日より前の案件を削除する
ワンショットスクリプト。

使い方:
  python cleanup_past_bids.py

動作:
  - 日本時間基準の「今日」を算出
  - bid_date が "YYYY/MM/DD" 形式で「今日より前」の案件を削除
  - bid_date が null/空文字の案件は残す（開札日未定のため）
"""

import os
import sys
import io
import json
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

JST = timezone(timedelta(hours=9))

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ .env に SUPABASE_URL と SUPABASE_SERVICE_KEY を設定してください")
    sys.exit(1)

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def preview_targets(today):
    """削除対象の一覧を取得（実削除の前に確認用）"""
    url = f"{SUPABASE_URL}/rest/v1/bids"
    params = {
        "and": f"(bid_date.gte.2000/01/01,bid_date.lt.{today})",
        "select": "case_id,name,bid_date",
        "limit": "10000",
    }
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def delete_past(today):
    """bid_date < today の案件を削除"""
    url = f"{SUPABASE_URL}/rest/v1/bids"
    params = {
        "and": f"(bid_date.gte.2000/01/01,bid_date.lt.{today})",
        "select": "id",
    }
    r = requests.delete(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    try:
        data = r.json() if r.text else []
        return len(data) if isinstance(data, list) else 0
    except Exception:
        return 0


def main():
    print("=" * 55)
    print(" 過去案件クリーンアップ（開札日超過分を削除）")
    print("=" * 55)

    today = datetime.now(JST).strftime("%Y/%m/%d")
    print(f"  基準日（日本時間）: {today}")

    print("\n[1/2] 削除対象を取得中...")
    try:
        targets = preview_targets(today)
    except Exception as e:
        print(f"  ❌ 取得失敗: {e}")
        return 1

    print(f"  対象: {len(targets)} 件")

    if not targets:
        print("\n  ✓ 削除対象なし")
        return 0

    # 最初の10件をプレビュー表示
    print("\n  プレビュー（最初の10件）:")
    for t in targets[:10]:
        cid = t.get("case_id", "?")
        name = (t.get("name") or "")[:40]
        bd = t.get("bid_date", "")
        print(f"    case_id={cid}  開札={bd}  {name}")
    if len(targets) > 10:
        print(f"    ... 他 {len(targets) - 10} 件")

    # 確認
    print(f"\n  上記 {len(targets)} 件を削除します。")
    ans = input("  実行しますか？ (yes/no): ").strip().lower()
    if ans not in ("yes", "y"):
        print("  キャンセルしました。")
        return 0

    print("\n[2/2] 削除中...")
    try:
        deleted = delete_past(today)
    except Exception as e:
        print(f"  ❌ 削除失敗: {e}")
        return 1

    print(f"  ✓ {deleted} 件を削除しました")
    return 0


if __name__ == "__main__":
    rc = main()
    if sys.platform == "win32":
        input("\nEnterキーを押して終了...")
    sys.exit(rc)
