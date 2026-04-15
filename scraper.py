"""
埼玉県入札情報公開システム スクレイパー (完全解析版)
=====================================================
確定した遷移フロー:
  工事等:
    POST /koukai/do/KK301ShowAction  (chotatsuType=00) → 検索フォーム
    POST /koukai/do/KK301SearchAction                  → 検索結果
  物品等:
    POST /koukai/do/KB301ShowAction  (chotatsuType=11) → 検索フォーム
    POST /koukai/do/KB301SearchAction                  → 検索結果

  表示件数: A300=040 (100件/ページ) が最大
"""

import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup
import json, re, time, os
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===== 設定 =====
BASE  = "https://ebidjk2.ebid2.pref.saitama.lg.jp"
START = BASE + "/koukai/do/KF000ShowAction"

# 工事等
KK_SHOW   = BASE + "/koukai/do/KK301ShowAction"
KK_SEARCH = BASE + "/koukai/do/KK301SearchAction"
# 物品等
KB_SHOW   = BASE + "/koukai/do/KB301ShowAction"
KB_SEARCH = BASE + "/koukai/do/KB301SearchAction"

OUTPUT_DIR  = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "bids.js")
CACHE_FILE  = os.path.join(OUTPUT_DIR, "geocode_cache.json")
CONFIG_FILE = os.path.join(OUTPUT_DIR, "search_config.json")

# ===== 検索設定の読み込み =====
# search_config.json がなければ「最新100件のみ（1ページ）」で実行する。
# アプリ内の「詳細検索」パネルから JSON をダウンロードして data/ に置くと、
# 次回 run.bat 実行時にその条件で取得される。
def load_search_config():
    defaults = {
        "max_pages":    1,              # 1ページ = 100件（デフォルト最速）
        "keyword":      "",             # 案件名キーワード（koujimei）
        "location":     "",             # 場所キーワード（koujibasho）
        "types":        ["00"],         # 00=工事等（建設工事特化）/ 11=物品等（既定OFF）
        "fetch_detail": False,          # 詳細URL取得（セッション依存のため通常は無効）
        "detail_limit": 100,            # 詳細取得する件数の上限（fetch_detail=Trueのとき有効）
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if isinstance(cfg, dict):
                defaults.update(cfg)
            print(f"  ✓ 検索設定を読み込みました: {CONFIG_FILE}")
        except Exception as e:
            print(f"  ⚠ 検索設定の読込に失敗（デフォルト使用）: {e}")
    else:
        print(f"  ℹ 検索設定なし → デフォルト（最新100件のみ）")
    return defaults

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
GEOCODE_INT = 1.2

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.7",
}
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===== セッション =====
def get_sid(html):
    m = re.search(r"jsessionid=([A-F0-9]+)", html, re.I)
    return m.group(1) if m else ""

def add_sid(url, sid):
    if sid and "jsessionid" not in url:
        return url + ";jsessionid=" + sid
    return url

def fetch(session, url, post=None, label="", referer=""):
    extra = {}
    if referer:
        extra["Referer"] = referer
    try:
        if post is not None:
            r = session.post(url, data=post, timeout=45, verify=False,
                             headers=extra)
        else:
            r = session.get(url, timeout=30, verify=False,
                            headers=extra)
        r.encoding = r.apparent_encoding or "shift_jis"
        # デバッグ: ステータスとサイズを出力
        print(f"    HTTP {r.status_code} | {len(r.content):,}bytes | {r.url[:80]}")
        return BeautifulSoup(r.text, "html.parser"), r.text, r.url
    except Exception as e:
        print(f"  [取得失敗] {label}: {e}")
        return None, "", url

# ===== 検索フォームの hidden フィールドを取得 =====
def get_hidden_fields(soup, form_name=None):
    """指定フォーム（または最初のフォーム）の hidden フィールドを返す"""
    if form_name:
        form = soup.find("form", {"name": form_name})
    else:
        form = soup.find("form")
    if not form:
        return {}
    fields = {}
    for inp in form.find_all("input", type="hidden"):
        name = inp.get("name", "")
        if name:
            fields[name] = inp.get("value", "")
    return fields

# ===== フレームページ専用テーブル解析 =====
def parse_frame_table(soup, chotatsu_type):
    """
    KFK/KFB301FrameShow のテーブルを解析する。
    ヘッダー行がなく、列位置が固定されているため専用関数で処理する。

    工事等(00) 列順: 案件名 | 案件番号 | 入札方式 | 案件状態 | 業種 | 場所 | 公開日 | 開札日 | 課所名 | 電子入札
    物品等(11) 列順: 案件名 | 案件番号 | 入札方式 | 案件状態 | 場所  | 公開日 | 開札日 | 課所名 | 電子入札
    """
    table = soup.find("table")
    if not table:
        return []

    # 工事等と物品等で列数・位置が異なる
    if chotatsu_type == "00":
        COL = {"name": 0, "number": 1, "method": 2, "status": 3,
               "category": 4, "location": 5, "notice_date": 6, "bid_date": 7,
               "org": 8, "ebid": 9}
    else:
        COL = {"name": 0, "number": 1, "method": 2, "status": 3,
               "location": 4, "notice_date": 5, "bid_date": 6,
               "org": 7, "ebid": 8}

    bids = []
    for row in table.find_all("tr"):
        cells = row.find_all(["td", "th"])
        min_cols = COL["org"] + 1
        if len(cells) < min_cols:
            continue

        def cv(key):
            idx = COL.get(key)
            if idx is not None and idx < len(cells):
                return cells[idx].get_text(strip=True)
            return ""

        # 案件名リンクから doEdit番号（内部ID）を取得
        case_id = ""
        name_link = cells[COL["name"]].find("a", href=True)
        if name_link:
            m = re.search(r"doEdit\('(\d+)'\)", name_link.get("href", ""), re.I)
            if m:
                case_id = m.group(1)

        # 電子入札リンクから ACN（受付番号）を取得
        acn = ""
        ebid_cell = cells[COL["ebid"]] if len(cells) > COL["ebid"] else None
        if ebid_cell:
            ebid_link = ebid_cell.find("a", href=True)
            if ebid_link:
                m = re.search(r"direct\('(\d+)'", ebid_link.get("href", ""), re.I)
                if m:
                    acn = m.group(1)

        name = cv("name")
        if not name or len(name) < 2:
            continue

        bids.append({
            "case_id":     case_id,
            "acn":         acn,
            "type":        chotatsu_type,  # "00"=工事等 / "11"=物品等
            "number":      cv("number"),
            "name":        name,
            "org":         cv("org"),
            "location":    cv("location"),
            "method":      cv("method"),
            "category":    cv("category"),
            "notice_date": cv("notice_date"),
            "bid_date":    cv("bid_date"),
            "price":       "",
            "detail_url":  "",   # 後で fetch_detail_url() で設定
            "lat": None, "lon": None,
        })

    return bids

# ===== 詳細ページのURLを取得（PDF公告書へのリンク）=====
# 詳細アクションURL（doEdit番号 → 詳細画面へ POST）
DETAIL_ACTIONS = {
    "00": BASE + "/koukai/do/KK301ReferAction",
    "11": BASE + "/koukai/do/KB301ReferAction",
}

def fetch_detail_url(session, chotatsu_type, case_id, sid, referer="", hidden=None):
    """
    doEdit番号を使って詳細ページにアクセスし、公告書PDFのURLを返す。
    PDFが見つからない場合は詳細ページ自体のURLを返す。
    hidden: 検索フォームの hidden フィールド（より正確なパラメータ送信に使用）
    """
    if not case_id:
        return ""

    action = DETAIL_ACTIONS.get(chotatsu_type, "")
    if not action:
        return ""

    url = add_sid(action, sid)

    # JSPパス（検索フォームで使用するものと同じ）
    if chotatsu_type == "00":
        jsp_path = "/WEB-INF/pages/pub_information/frontsite/KFK301.jsp"
    else:
        jsp_path = "/WEB-INF/pages/pub_information/frontsite/KFB301.jsp"

    base_hidden = hidden or {}

    # 検索フォームの hidden フィールドを引き継ぎ、control_no を対象案件に設定
    post_data = {
        "honGamenJspPath":    jsp_path,
        "chotatsuType":       chotatsu_type,
        "select_kikan":       "0000ZZZZZZ",
        "control_no":         case_id,
        "postconv_flg":       base_hidden.get("postconv_flg", "1"),
        "initFlg":            base_hidden.get("initFlg", "null"),
        "editmode":           base_hidden.get("editmode", ""),
        "trader_id":          base_hidden.get("trader_id", ""),
        "leave_branchi_flg":  base_hidden.get("leave_branchi_flg", ""),
        "SUPPLYTYPE":         base_hidden.get("SUPPLYTYPE", ""),
        "supplytype":         "",
        "hachukikan":         "",
        "bukyoku":            "",
        "kakakari":           "",
        "A300":               "040",
    }

    try:
        headers = {}
        if referer:
            headers["Referer"] = referer
        r = session.post(url, data=post_data, timeout=20, verify=False,
                         headers=headers)

        # SearchAction / ShowAction へリダイレクトされた場合はPOST失敗とみなす
        result_url = str(r.url)
        if "SearchAction" in result_url or "ShowAction" in result_url:
            return ""

        # 詳細ページのURLをそのまま返す（PDFではなくHTMLページ）
        return result_url

    except Exception:
        return ""

# ===== ページネーション判定 =====
def find_next_page(soup):
    """次ページへの情報を返す。(type, data): type='post'|'get', data=dict|url"""

    # 1. 「次へ」submitボタン
    for inp in soup.find_all("input", type=["submit","button","image"]):
        val = inp.get("value", "")
        if re.search(r"次[へページ頁]|NEXT|>>", val):
            return "submit_btn", inp

    # 2. 「次へ」リンク
    for a in soup.find_all("a"):
        txt = a.get_text(strip=True)
        href = a.get("href", "")
        if re.search(r"次[へページ頁]|NEXT|>>", txt):
            if href and not href.startswith("javascript"):
                url = BASE + href if href.startswith("/") else BASE + "/koukai/do/" + href
                return "get", url

    return None, None

# ===== 1種別の発注情報を全件取得 =====
def scrape_type(session, chotatsu_type, label, show_url, search_url, sid, config=None):
    if config is None:
        config = {"max_pages": 1, "keyword": "", "location": "",
                  "fetch_detail": True, "detail_limit": 100}
    print(f"\n  ── {label} ──")

    # 工事等(KK) → KFK301FrameShow、物品等(KB) → KFB301FrameShow
    if "KK" in show_url:
        frame_url = BASE + "/koukai/do/KFK301FrameShow"
        jsp_path  = "/WEB-INF/pages/pub_information/frontsite/KFK301.jsp"
    else:
        frame_url = BASE + "/koukai/do/KFB301FrameShow"
        jsp_path  = "/WEB-INF/pages/pub_information/frontsite/KFB301.jsp"

    # STEP A: 検索フォームを取得
    post_a = {
        "chotatsuType":  chotatsu_type,
        "select_kikan":  "0000ZZZZZZ",
        "auth":          "",
        "gyosyu_type":   "",
    }
    soup_form, raw_form, form_actual_url = fetch(
        session, add_sid(show_url, sid),
        post=post_a, label=f"フォーム({label})")
    if not soup_form:
        print(f"  [{label}] フォーム取得失敗")
        return []

    new_sid = get_sid(raw_form) or get_sid(str(form_actual_url))
    if new_sid:
        sid = new_sid

    hidden = get_hidden_fields(soup_form)
    print(f"  [{label}] hidden: {list(hidden.keys())}")

    form_url_clean = re.sub(r";jsessionid=[A-F0-9]+", "", str(form_actual_url), flags=re.I)
    search_url_with_sid = add_sid(search_url, sid)

    # STEP B: SearchAction に POST して検索実行
    def do_search(searchflg_val, extra_post=None):
        p = {
            "honGamenJspPath":        jsp_path,
            "supplytype":             "",
            "hachukikan":             "",
            "bukyoku":                "",
            "kakakari":               "",
            "kasho_name":             "",
            "A303":                   "",
            "shubetsu1":              "",
            "kakudzuke":              "",
            "koujimei":               config.get("keyword", "") or "",
            "koujibangou":            "",
            "koujibasho":             config.get("location", "") or "",
            "selectdate":             "1",
            "YEARBEGIN":              "",
            "koukokubi_kaishi_tsuki": "",
            "koukokubi_kaishi_nichi": "",
            "koukokubi_kaishi":       "",
            "YEAREND":                "",
            "koukokubi_owari_tsuki":  "",
            "koukokubi_owari_nichi":  "",
            "koukokubi_owari":        "",
            "yearend_check_flg":      "1",
            "A300":                   "040",
            "initFlg":                hidden.get("initFlg", "null"),
            "searchflg":              searchflg_val,
            "control_no":             hidden.get("control_no", ""),
            "editmode":               hidden.get("editmode", ""),
            "trader_id":              hidden.get("trader_id", ""),
            "leave_branchi_flg":      hidden.get("leave_branchi_flg", ""),
            "postconv_flg":           hidden.get("postconv_flg", "1"),
            "SUPPLYTYPE":             hidden.get("SUPPLYTYPE", ""),
            "chotatsuType":           chotatsu_type,
            "select_kikan":           "0000ZZZZZZ",
        }
        if extra_post:
            p.update(extra_post)
        return fetch(session, search_url_with_sid,
                     post=p, label=f"検索({label},flg={searchflg_val})",
                     referer=form_url_clean)

    print(f"  [{label}] 検索実行 → {search_url}")
    soup_outer, raw_outer, res_url = do_search("1")
    if not soup_outer:
        print(f"  [{label}] 検索結果取得失敗")
        return []

    # デバッグ保存（外側ページ）
    debug_path = os.path.join(OUTPUT_DIR, f"debug_search_{chotatsu_type}.html")
    with open(debug_path, "w", encoding="utf-8") as f:
        f.write(raw_outer)
    print(f"  [{label}] 外側ページ保存: {debug_path} ({len(raw_outer):,}文字)")

    # 全件確認ダイアログ対応 (PQBE0001I / PQBE0004I)
    for attempt, flg in enumerate(["2", "3"], start=1):
        if "PQBE0001I" not in raw_outer and "PQBE0004I" not in raw_outer:
            break
        print(f"  [{label}] 全件確認ダイアログ({attempt}回目) → searchflg={flg} で再送")
        soup_outer, raw_outer, res_url = do_search(flg)
        if not soup_outer:
            return []
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(raw_outer)

    # 総ページ数を外側ページから取得
    m = re.search(r'name="hiddentotalpages"[^>]+value="(\d+)"', raw_outer)
    if not m:
        m = re.search(r'hiddentotalpages[^>]+value=["\'](\d+)', raw_outer)
    total_pages = int(m.group(1)) if m else 1
    print(f"  [{label}] 総ページ数: {total_pages}")

    if total_pages == 0:
        print(f"  [{label}] 該当データなし")
        return []

    # STEP C: iframe（KFK/KFB301FrameShow）から実データを取得してページ送り
    all_bids = []
    current_res_url = str(res_url)

    max_pages = max(1, int(config.get("max_pages", 1)))
    pages_to_fetch = min(total_pages, max_pages)
    print(f"  [{label}] 取得ページ数: {pages_to_fetch} / {total_pages}")
    for page in range(1, pages_to_fetch + 1):
        if page > 1:
            time.sleep(0.8)
            # GET でページ移動（外側フレームのページ番号を更新）
            page_get_url = add_sid(search_url, sid) + f"?curPage={page}"
            fetch(session, page_get_url, label=f"ページ移動p{page}({label})")

        # iframe の実データ取得
        soup_frame, raw_frame, _ = fetch(
            session, add_sid(frame_url, sid),
            label=f"フレームデータp{page}({label})")

        if not soup_frame:
            print(f"  [{label}] p{page}: フレーム取得失敗")
            break

        # デバッグ: フレームHTMLを1ページ目のみ保存
        if page == 1:
            frame_debug = os.path.join(OUTPUT_DIR, f"debug_frame_{chotatsu_type}.html")
            with open(frame_debug, "w", encoding="utf-8") as f:
                f.write(raw_frame)
            print(f"  [{label}] フレーム保存: {frame_debug} ({len(raw_frame):,}文字)")

        # parse_frame_table で正確に解析
        bids = parse_frame_table(soup_frame, chotatsu_type)
        if not bids:
            txt = soup_frame.get_text(separator=" ", strip=True)
            if page == 1:
                if "該当する" in txt and "存在しません" in txt:
                    print(f"  [{label}] 該当データなし")
                else:
                    print(f"  [{label}] p{page}: データ未検出。内容: {txt[:300]}")
            break

        all_bids.extend(bids)
        print(f"  [{label}] p{page}/{total_pages}: {len(bids)}件 (累計{len(all_bids)}件)")

    # 詳細URL（公告書PDF）を取得 ── 表示対象になる新しい順N件のみ
    if all_bids and config.get("fetch_detail", True):
        all_bids.sort(key=lambda b: b.get("notice_date", "") or "", reverse=True)
        detail_limit = max(0, int(config.get("detail_limit", 100)))
        target = all_bids[:detail_limit]
        referer = re.sub(r";jsessionid=[A-F0-9]+", "", search_url, flags=re.I)
        print(f"  [{label}] 詳細URL取得中（最新{len(target)}件）...")
        for i, bid in enumerate(target):
            if not bid.get("case_id"):
                continue
            url = fetch_detail_url(session, chotatsu_type, bid["case_id"], sid, referer, hidden=hidden)
            if url:
                bid["detail_url"] = url
            if (i + 1) % 10 == 0:
                print(f"    {i + 1}/{len(target)} 件完了")
            time.sleep(0.3)

    return all_bids

# ===== ジオコーダー =====
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def geocode(addr, cache):
    if not addr:
        return None, None
    key = addr.strip()
    if key in cache:
        return cache[key].get("lat"), cache[key].get("lon")
    q = key if re.search(r"埼玉|さいたま", key) else "埼玉県" + key
    try:
        time.sleep(GEOCODE_INT)
        r = requests.get(GEOCODE_URL,
                         params={"q": q, "format": "json", "limit": 1, "countrycodes": "jp"},
                         headers={"User-Agent": "SaitamaBidMapApp/1.0"},
                         timeout=10)
        data = r.json()
        if data:
            lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
            cache[key] = {"lat": lat, "lon": lon}
            save_cache(cache)
            return lat, lon
    except Exception as e:
        print(f"    ジオコーディングエラー: {e}")
    cache[key] = {"lat": None, "lon": None}
    save_cache(cache)
    return None, None

# ===== メイン =====
def main():
    print("=" * 55)
    print(" 埼玉県 建設工事 入札情報マップ - データ取得")
    print(f" {datetime.now():%Y/%m/%d %H:%M:%S}")
    print("=" * 55)

    config = load_search_config()
    print(f"  設定: max_pages={config['max_pages']}, keyword='{config.get('keyword','')}', "
          f"types={config['types']}, fetch_detail={config['fetch_detail']}")

    session = requests.Session()
    session.headers.update(HEADERS)

    # 1. セッション確立
    print("\n[1/4] サイトに接続中...")
    soup0, raw0, _ = fetch(session, START, label="フレームセット")
    if not soup0:
        print("  接続失敗")
        return []
    sid = get_sid(raw0)

    # フレームのメインページも取得してセッションを固定
    frames = re.findall(r'src="([^"]+)"', raw0)
    main_src = next((f for f in frames if "main" in f.lower() or "right" in f.lower()), "")
    if main_src:
        main_path = re.sub(r";jsessionid=[A-F0-9]+", "", main_src, flags=re.I)
        _, raw_main, _ = fetch(session, BASE + main_path, label="トップメニュー")
        new_sid = get_sid(raw_main)
        if new_sid:
            sid = new_sid
    print(f"  ✓ 接続成功  セッション: {sid[:12] if sid else '(Cookie)'}...")

    # 2 & 3. 発注情報取得（工事等 + 物品等）
    print("\n[2/4] 発注情報を取得中...")
    all_bids = []

    if "00" in config["types"]:
        bids_kk = scrape_type(session, "00", "工事等",
                              KK_SHOW, KK_SEARCH, sid, config)
        all_bids.extend(bids_kk)
    else:
        print("  [工事等] スキップ（設定で無効）")

    if "11" in config["types"]:
        bids_kb = scrape_type(session, "11", "物品等",
                              KB_SHOW, KB_SEARCH, sid, config)
        all_bids.extend(bids_kb)
    else:
        print("  [物品等] スキップ（設定で無効）")

    print(f"\n  合計: {len(all_bids)} 件")

    if not all_bids:
        print("\n  ⚠ データが取得できませんでした。")
        print("  data/debug_search_00.html を Claude に送ってください。")
        return []

    # 4. ジオコーディング
    print("\n[3/4] 住所を座標変換中...")
    cache = load_cache()
    ok = 0
    for i, bid in enumerate(all_bids):
        loc = (bid.get("location") or "").strip()
        if not loc:
            continue
        if loc in cache and cache[loc].get("lat"):
            bid["lat"] = cache[loc]["lat"]
            bid["lon"] = cache[loc]["lon"]
            ok += 1
            continue
        print(f"  [{i+1}/{len(all_bids)}] {loc}")
        lat, lon = geocode(loc, cache)
        bid["lat"] = lat
        bid["lon"] = lon
        if lat:
            ok += 1
    print(f"  ✓ {ok} 件の座標変換完了")

    return all_bids

def save(bids):
    mappable   = sum(1 for b in bids if b.get("lat"))
    unmappable = len(bids) - mappable
    meta = {
        "total":      len(bids),
        "mappable":   mappable,
        "unmappable": unmappable,
        "fetched_at": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "source_url": START,
    }
    js = (f"// 入札情報データ ({meta['fetched_at']})\n"
          f"const BID_DATA = {json.dumps(bids, ensure_ascii=False, indent=2)};\n"
          f"const BID_META = {json.dumps(meta,  ensure_ascii=False, indent=2)};\n")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"\n[4/4] ✓ 保存: {OUTPUT_FILE}")
    print(f"  地図表示可能: {mappable} 件 / 座標なし: {unmappable} 件")

def make_sample():
    sample = [
        {"number":"S-001","name":"（サンプル）さいたま市内道路舗装工事","org":"埼玉県 県土整備部","location":"さいたま市大宮区","method":"条件付一般競争入札","category":"工事","notice_date":"2024/04/01","bid_date":"2024/04/15","price":"","detail_url":START,"lat":35.9064,"lon":139.6234},
        {"number":"S-002","name":"（サンプル）荒川護岸改修工事","org":"埼玉県 県土整備部","location":"川口市","method":"一般競争入札","category":"工事","notice_date":"2024/04/02","bid_date":"2024/04/18","price":"","detail_url":START,"lat":35.8060,"lon":139.7199},
        {"number":"S-003","name":"（サンプル）秩父市内橋梁補修工事","org":"埼玉県 県土整備部","location":"秩父市","method":"条件付一般競争入札","category":"工事","notice_date":"2024/04/03","bid_date":"2024/04/20","price":"","detail_url":START,"lat":35.9919,"lon":139.0863},
    ]
    meta = {"total":len(sample),"mappable":len(sample),"unmappable":0,
            "fetched_at":datetime.now().strftime("%Y/%m/%d %H:%M:%S")+"（サンプル）",
            "source_url":START}
    js = (f"// サンプルデータ\nconst BID_DATA = "
          f"{json.dumps(sample, ensure_ascii=False, indent=2)};\n"
          f"const BID_META = {json.dumps(meta, ensure_ascii=False, indent=2)};\n")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"✓ サンプルデータ保存: {OUTPUT_FILE}")

if __name__ == "__main__":
    bids = main()
    if bids:
        save(bids)
        print("\n" + "="*55)
        print("完了！ index.html をブラウザで開いてください。")
        print("="*55)
    else:
        print("\nサンプルデータを生成します...")
        make_sample()
        print("\n data/debug_search_00.html を Claude に送ってください。")
    print()
    input("Enterキーを押して終了...")
