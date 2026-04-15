import { createClient } from "@supabase/supabase-js";
import type { Bid } from "@/lib/supabase";
import MapPage from "@/components/MapPage";

// Vercel のキャッシュを回避し、ビルドごとに最新データを取得
export const revalidate = 600; // 10分に1回再検証

async function getBids(): Promise<{ bids: Bid[]; fetchedAt: string | null }> {
  const url  = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !anon) {
    console.error("Supabase 環境変数が未設定です");
    return { bids: [], fetchedAt: null };
  }

  const supabase = createClient(url, anon, { auth: { persistSession: false } });

  // 日本時間基準の「今日」を "YYYY/MM/DD" 形式で作る
  // （Vercelのサーバーは UTC 稼働のため、ローカル時刻では判定が1日ずれる可能性がある）
  const todayStr = new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  })
    .format(new Date())
    .replace(/-/g, "/");

  // 建設工事のみ（type='00'）、新しい順、最大2000件
  // 開札日が今日以降、または未設定の案件のみ表示（開札済みは自動で非表示）
  const { data, error } = await supabase
    .from("bids")
    .select("*")
    .eq("type", "00")
    .or(`bid_date.is.null,bid_date.eq.,bid_date.gte.${todayStr}`)
    .order("notice_date", { ascending: false })
    .limit(2000);

  if (error) {
    console.error("Supabase 取得エラー:", error);
    return { bids: [], fetchedAt: null };
  }

  // 最終更新日時
  const { data: meta } = await supabase
    .from("meta")
    .select("value, updated_at")
    .eq("key", "last_scrape")
    .maybeSingle();

  const fetchedAt = meta?.updated_at ?? null;

  return { bids: (data ?? []) as Bid[], fetchedAt };
}

export default async function Home() {
  const { bids, fetchedAt } = await getBids();
  return <MapPage bids={bids} fetchedAt={fetchedAt} />;
}
