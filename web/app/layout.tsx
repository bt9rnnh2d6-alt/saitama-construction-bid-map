import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "埼玉県 建設工事 入札情報マップ",
  description:
    "埼玉県で発注される建設工事の入札案件を地図上で検索できるサービス。工種・入札方式・発注機関で絞り込み可能。",
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ja">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        />
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"
        />
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
