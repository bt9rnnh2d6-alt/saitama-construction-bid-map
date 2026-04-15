"use client";

import { useState, useMemo, useEffect } from "react";
import dynamic from "next/dynamic";
import type { Bid } from "@/lib/supabase";

// Leaflet は SSR 不可なので client-only で読み込み
const MapView = dynamic(() => import("./MapView"), {
  ssr: false,
  loading: () => <div className="loading">地図を読み込み中...</div>,
});

const DISPLAY_LIMIT = 500;

type Props = {
  bids: Bid[];
  fetchedAt: string | null;
};

export default function MapPage({ bids, fetchedAt }: Props) {
  const [query, setQuery]       = useState("");
  const [category, setCategory] = useState("");
  const [method, setMethod]     = useState("");
  const [org, setOrg]           = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(null);

  // フィルタ適用
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return bids.filter((b) => {
      if (q) {
        const hay =
          (b.name || "") + " " + (b.org || "") + " " + (b.location || "");
        if (!hay.toLowerCase().includes(q)) return false;
      }
      if (category && b.category !== category) return false;
      if (method   && b.method   !== method)   return false;
      if (org      && b.org      !== org)      return false;
      return true;
    });
  }, [bids, query, category, method, org]);

  const displayed = filtered.slice(0, DISPLAY_LIMIT);

  // フィルタ選択肢
  const categories = useMemo(
    () => [...new Set(bids.map((b) => b.category).filter(Boolean))].sort() as string[],
    [bids]
  );
  const methods = useMemo(
    () => [...new Set(bids.map((b) => b.method).filter(Boolean))].sort() as string[],
    [bids]
  );
  const orgs = useMemo(
    () => [...new Set(bids.map((b) => b.org).filter(Boolean))].sort() as string[],
    [bids]
  );

  const withMap = displayed.filter((b) => b.lat && b.lon).length;
  const unmappable = displayed.length - withMap;

  const reset = () => {
    setQuery("");
    setCategory("");
    setMethod("");
    setOrg("");
  };

  const formattedDate = fetchedAt
    ? new Date(fetchedAt).toLocaleString("ja-JP", {
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit",
      })
    : "不明";

  return (
    <>
      <header>
        <h1>
          <span>🏗️</span>
          埼玉県 建設工事 入札情報マップ
        </h1>
        <div className="meta">
          全 {bids.length} 件 / 最終更新: {formattedDate}
        </div>
      </header>

      <div className="main-container">
        <div id="sidebar">
          <div className="filter-area">
            <input
              type="text"
              placeholder="🔍 案件名・機関名・場所で検索..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <div className="filter-row">
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">工種: すべて</option>
                {categories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <select value={method} onChange={(e) => setMethod(e.target.value)}>
                <option value="">入札方式: すべて</option>
                {methods.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
            <div className="filter-row">
              <select value={org} onChange={(e) => setOrg(e.target.value)}>
                <option value="">発注機関: すべて</option>
                {orgs.map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
              <button className="btn-reset" onClick={reset}>リセット</button>
            </div>
          </div>

          <div className="count-bar">
            <strong>{filtered.length}</strong> 件
            {filtered.length > DISPLAY_LIMIT && (
              <span style={{ color: "#e65100" }}>
                {" "}（最新 {DISPLAY_LIMIT} 件を表示）
              </span>
            )}
            （地図表示: <strong>{withMap}</strong> 件）
          </div>

          <div id="bid-list">
            {displayed.length === 0 ? (
              <div style={{ padding: 20, textAlign: "center", color: "#999" }}>
                該当する案件がありません
              </div>
            ) : (
              displayed.map((b) => (
                <div
                  key={b.id}
                  className="bid-item"
                  onClick={() => setSelectedId(b.id)}
                >
                  <div className="name">{b.name}</div>
                  <div className="meta">
                    {b.category && <span className="label">{b.category}</span>}
                    {b.org && <span>{b.org}</span>}
                  </div>
                  <div className="meta">
                    {b.location && <>📍 {b.location}　</>}
                    {b.bid_date && <>🗓 開札 {b.bid_date}</>}
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="sidebar-footer">
            データ出典：埼玉県 電子入札システム（公開情報）
          </div>
        </div>

        <div id="map-container">
          <MapView bids={displayed} selectedId={selectedId} />
          <div id="stats-panel">
            <div className="stat-row">
              表示中: <strong>{withMap}</strong> 件
            </div>
            <div className="stat-row">
              地図表示不可: <strong>{unmappable}</strong> 件
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
