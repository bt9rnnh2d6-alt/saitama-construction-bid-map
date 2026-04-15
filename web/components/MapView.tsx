"use client";

import { useEffect, useRef } from "react";
import type { Bid } from "@/lib/supabase";

type Props = {
  bids: Bid[];
  selectedId: number | null;
};

function escapeHtml(s: string | null | undefined): string {
  if (!s) return "";
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// 埼玉県 入札情報公開システムの公開入口（フレームセット）
// 各案件ごとの直接URLはセッション依存で作れないため、
// 公式サイトの入口に遷移し、案件番号で検索してもらう運用とする。
const SAITAMA_OFFICIAL_URL =
  "https://ebidjk2.ebid2.pref.saitama.lg.jp/koukai/do/KF000ShowAction";

function popupHtml(b: Bid): string {
  const rowsBase: Array<[string, string]> = [
    ["工種",   b.category || "—"],
    ["発注",   b.org      || "—"],
    ["場所",   b.location || "—"],
    ["方式",   b.method   || "—"],
    ["公告日", b.notice_date || "—"],
    ["開札日", b.bid_date    || "—"],
  ];
  const rows = rowsBase.filter(([, v]) => v && v !== "—") as Array<[string, string]>;

  const body = rows
    .map(
      ([k, v]) =>
        `<div class="popup-row"><span class="k">${escapeHtml(k)}</span>${escapeHtml(v)}</div>`
    )
    .join("");

  // 案件番号行（コピー用ボタン付き）
  const numberHtml = b.number
    ? `<div class="popup-row popup-number">
         <span class="k">案件番号</span>
         <span class="popup-number-val">${escapeHtml(b.number)}</span>
         <button type="button" class="popup-copy-btn"
                 data-copy="${escapeHtml(b.number)}"
                 title="案件番号をコピー">コピー</button>
       </div>`
    : "";

  // 公式サイトの入口へのボタン（案件番号を検索語としてコピー済みの前提で誘導）
  const linkHtml = `
    <a class="popup-btn"
       href="${SAITAMA_OFFICIAL_URL}"
       target="_blank" rel="noopener">
      埼玉県公式サイトで検索 →
    </a>
    <div class="popup-hint">※ 公式サイトで案件番号を貼り付けて検索してください</div>
  `;

  return `
    <div>
      <div class="popup-title">${escapeHtml(b.name)}</div>
      ${numberHtml}
      ${body}
      ${linkHtml}
    </div>
  `;
}

export default function MapView({ bids, selectedId }: Props) {
  const mapRef   = useRef<HTMLDivElement>(null);
  const leafletMap = useRef<any>(null);
  const clusterRef = useRef<any>(null);
  const markerIndex = useRef<Map<number, any>>(new Map());

  // 初回マウント: 地図初期化
  useEffect(() => {
    if (!mapRef.current) return;
    let cancelled = false;

    (async () => {
      const L = (await import("leaflet")).default;
      await import("leaflet.markercluster");

      if (cancelled || !mapRef.current) return;

      // StrictMode の二重発火対策: 既に初期化済みならスキップ
      if ((mapRef.current as any)._leaflet_id != null || leafletMap.current) {
        return;
      }

      const map = L.map(mapRef.current, {
        center: [36.0, 139.5],
        zoom: 9,
        zoomControl: true,
      });

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 18,
        attribution:
          '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(map);

      // @ts-ignore
      const cluster = L.markerClusterGroup({
        maxClusterRadius: 50,
        spiderfyOnMaxZoom: true,
      });
      map.addLayer(cluster);

      // ポップアップ内「コピー」ボタン押下で案件番号をクリップボードへ
      map.on("popupopen", (e: any) => {
        const el: HTMLElement | undefined = e?.popup?.getElement?.();
        if (!el) return;
        const btn = el.querySelector<HTMLButtonElement>(".popup-copy-btn");
        if (!btn || btn.dataset.bound === "1") return;
        btn.dataset.bound = "1";
        btn.addEventListener("click", async () => {
          const txt = btn.getAttribute("data-copy") || "";
          try {
            await navigator.clipboard.writeText(txt);
          } catch {
            // フォールバック: 旧ブラウザ用
            const ta = document.createElement("textarea");
            ta.value = txt;
            document.body.appendChild(ta);
            ta.select();
            try { document.execCommand("copy"); } catch {}
            document.body.removeChild(ta);
          }
          const original = btn.textContent || "コピー";
          btn.textContent = "コピー済み";
          btn.classList.add("copied");
          setTimeout(() => {
            btn.textContent = original;
            btn.classList.remove("copied");
          }, 1500);
        });
      });

      leafletMap.current = map;
      clusterRef.current = cluster;
    })();

    return () => {
      cancelled = true;
      if (leafletMap.current) {
        leafletMap.current.remove();
        leafletMap.current = null;
        clusterRef.current = null;
      }
    };
  }, []);

  // bids 変更時: マーカー再構築
  useEffect(() => {
    const map = leafletMap.current;
    const cluster = clusterRef.current;
    if (!map || !cluster) return;

    (async () => {
      const L = (await import("leaflet")).default;
      cluster.clearLayers();
      markerIndex.current.clear();

      // 埼玉県の境界ボックス（ざっくり矩形）
      // 万一スクレイパー側の修正漏れで県外座標が混入しても地図には出さない安全網
      const SAITAMA_BBOX = {
        minLat: 35.7473, maxLat: 36.2836,
        minLon: 138.7107, maxLon: 139.9003,
      };
      const inSaitama = (lat: number, lon: number) =>
        lat >= SAITAMA_BBOX.minLat && lat <= SAITAMA_BBOX.maxLat &&
        lon >= SAITAMA_BBOX.minLon && lon <= SAITAMA_BBOX.maxLon;

      const mappable = bids.filter(
        (b) =>
          b.lat != null && b.lon != null &&
          inSaitama(b.lat as number, b.lon as number)
      );
      mappable.forEach((b) => {
        const m = L.marker([b.lat as number, b.lon as number], {
          title: b.name,
        });
        m.bindPopup(popupHtml(b), { maxWidth: 320 });
        cluster.addLayer(m);
        markerIndex.current.set(b.id, m);
      });

      if (mappable.length > 0 && !map._fitted) {
        const bounds = L.latLngBounds(
          mappable.map((b) => [b.lat as number, b.lon as number])
        );
        map.fitBounds(bounds, { padding: [30, 30], maxZoom: 12 });
        map._fitted = true;
      }
    })();
  }, [bids]);

  // 選択案件へフォーカス
  useEffect(() => {
    if (selectedId == null) return;
    const map = leafletMap.current;
    const m = markerIndex.current.get(selectedId);
    if (map && m) {
      map.setView(m.getLatLng(), Math.max(map.getZoom(), 13), { animate: true });
      m.openPopup();
    }
  }, [selectedId]);

  return <div id="map" ref={mapRef} style={{ width: "100%", height: "100%" }} />;
}
