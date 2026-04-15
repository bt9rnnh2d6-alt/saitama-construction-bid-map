"""
入札情報マップ ローカルサーバー
================================
run.bat から自動起動されます。
役割:
  - index.html / data/ 以下の静的ファイルを配信
  - /detail?case_id=XXX&type=00 → 公式サイトの詳細ページを取得して返す
  ※ 社内用途のみ。外部には公開しないでください。
"""

import sys, io
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import os, re, mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PORT    = 8765
BASE    = "https://ebidjk2.ebid2.pref.saitama.lg.jp"
START   = BASE + "/koukai/do/KF000ShowAction"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,*/*;q=0.9",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.7",
}

DETAIL_ACTIONS = {
    "00": BASE + "/koukai/do/KK301ReferAction",
    "11": BASE + "/koukai/do/KB301ReferAction",
}
SHOW_ACTIONS = {
    "00": BASE + "/koukai/do/KK301ShowAction",
    "11": BASE + "/koukai/do/KB301ShowAction",
}

# ===== セッション管理 =====
_session = None
_sid     = ""

def get_sid(text):
    m = re.search(r"jsessionid=([A-F0-9]+)", text, re.I)
    return m.group(1) if m else ""

def add_sid(url):
    if _sid and "jsessionid" not in url:
        return url + ";jsessionid=" + _sid
    return url

def init_session():
    """公式サイトにアクセスしてセッションを確立する"""
    global _session, _sid
    _session = requests.Session()
    _session.headers.update(HEADERS)
    try:
        r = _session.get(START, verify=False, timeout=15)
        _sid = get_sid(r.text) or get_sid(str(r.url))
        print(f"  セッション確立: {_sid[:12] if _sid else '(Cookie)'}...")
    except Exception as e:
        print(f"  セッション確立失敗（後で再試行します）: {e}")

def ensure_session():
    """セッションがなければ初期化する"""
    global _session
    if _session is None:
        init_session()

# ===== 詳細ページ取得 =====
def fix_urls(html):
    """相対URLを絶対URLに変換し、文字コードをUTF-8に統一する"""
    html = re.sub(r'href="(/[^"]*)"',   f'href="{BASE}\\1"',   html)
    html = re.sub(r"href='(/[^']*)'",   f"href='{BASE}\\1'",   html)
    html = re.sub(r'src="(/[^"]*)"',    f'src="{BASE}\\1"',    html)
    html = re.sub(r'action="(/[^"]*)"', f'action="{BASE}\\1"', html)
    html = re.sub(r'charset=["\']?Shift[_-]JIS["\']?', 'charset="UTF-8"', html, flags=re.I)
    return html

def get_hidden_fields(soup):
    form = soup.find("form")
    if not form:
        return {}
    return {
        inp.get("name", ""): inp.get("value", "")
        for inp in form.find_all("input", type="hidden")
        if inp.get("name")
    }

def fetch_detail(case_id, chotatsu_type):
    """case_id を使って公式サイトの詳細ページを取得する"""
    global _sid
    ensure_session()

    action = DETAIL_ACTIONS.get(chotatsu_type, DETAIL_ACTIONS["00"])

    # ① ShowAction でセッションを更新し hidden フィールドを取得
    show_url = SHOW_ACTIONS.get(chotatsu_type, SHOW_ACTIONS["00"])
    try:
        r0 = _session.post(add_sid(show_url), data={
            "chotatsuType":  chotatsu_type,
            "select_kikan":  "0000ZZZZZZ",
            "auth":          "",
            "gyosyu_type":   "",
        }, verify=False, timeout=15)
        r0.encoding = r0.apparent_encoding or "shift_jis"
        new_sid = get_sid(r0.text) or get_sid(str(r0.url))
        if new_sid:
            _sid = new_sid
        hidden = get_hidden_fields(BeautifulSoup(r0.text, "html.parser"))
    except Exception:
        hidden = {}

    # ② ReferAction で詳細ページを取得
    post_data = {
        "chotatsuType":      chotatsu_type,
        "select_kikan":      "0000ZZZZZZ",
        "control_no":        case_id,
        "postconv_flg":      hidden.get("postconv_flg", "1"),
        "initFlg":           hidden.get("initFlg", "1"),
        "editmode":          hidden.get("editmode", ""),
        "trader_id":         hidden.get("trader_id", ""),
        "leave_branchi_flg": hidden.get("leave_branchi_flg", ""),
        "SUPPLYTYPE":        hidden.get("SUPPLYTYPE", ""),
    }

    try:
        r = _session.post(add_sid(action), data=post_data, verify=False, timeout=20,
                          headers={"Referer": show_url})
        r.encoding = r.apparent_encoding or "shift_jis"
        result_url = str(r.url)

        # SearchAction にリダイレクトされた場合はセッション切れ → 再初期化
        if "SearchAction" in result_url or "ShowAction" in result_url:
            print("  セッション切れ → 再初期化中...")
            init_session()
            return fetch_detail(case_id, chotatsu_type)  # 1回だけ再試行

        html = fix_urls(r.text)
        return 200, html.encode("utf-8", errors="replace")

    except Exception as e:
        body = f"""<html><head><meta charset="UTF-8"></head><body>
            <h2>取得エラー</h2><p>{e}</p>
            <p><a href="{START}" target="_blank">公式サイトを直接開く</a></p>
        </body></html>"""
        return 500, body.encode("utf-8")

# ===== HTTP サーバー =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # アクセスログを最小限にする
        if "/detail" in args[0] if args else False:
            print(f"  [詳細取得] {args[0]}")

    def send_bytes(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        # ローカル環境のみなので CORS は緩く設定
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)

        # ----- /detail エンドポイント -----
        if parsed.path == "/detail":
            case_id      = unquote(qs.get("case_id", [""])[0])
            chotatsu_type = qs.get("type", ["00"])[0]

            if not case_id:
                self.send_bytes(400, "text/plain; charset=utf-8", "case_id が必要です".encode("utf-8"))
                return

            print(f"  [詳細] case_id={case_id} type={chotatsu_type}")
            code, body = fetch_detail(case_id, chotatsu_type)
            self.send_bytes(code, "text/html; charset=utf-8", body)
            return

        # ----- 静的ファイル配信 -----
        rel = parsed.path.lstrip("/") or "index.html"
        filepath = os.path.normpath(os.path.join(BASE_DIR, rel))

        # ディレクトリトラバーサル防止
        if not filepath.startswith(BASE_DIR):
            self.send_bytes(403, "text/plain", b"Forbidden")
            return

        if os.path.isfile(filepath):
            ctype, _ = mimetypes.guess_type(filepath)
            ctype = ctype or "application/octet-stream"
            if "text" in ctype and "charset" not in ctype:
                ctype += "; charset=utf-8"
            with open(filepath, "rb") as f:
                body = f.read()
            self.send_bytes(200, ctype, body)
        else:
            self.send_bytes(404, "text/plain; charset=utf-8", b"Not Found")


if __name__ == "__main__":
    print("=" * 50)
    print(" 入札情報マップ ローカルサーバー")
    print(f" http://localhost:{PORT}/")
    print(" ※このウィンドウを開いている間、サーバーが動作します")
    print("=" * 50)

    ensure_session()

    server = HTTPServer(("localhost", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")
