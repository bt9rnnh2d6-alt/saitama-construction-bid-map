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

  // 建設工事のみ（type='00'）、新しい順、最大2000件
  const { data, error } = await supabase
    .from("bids")
    .select("*")
    .eq("type", "00")
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
