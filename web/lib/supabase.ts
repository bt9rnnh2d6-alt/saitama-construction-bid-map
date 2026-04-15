import { createClient } from "@supabase/supabase-js";

const url  = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(url, anon, {
  auth: { persistSession: false },
});

export type Bid = {
  id:          number;
  case_id:     string;
  acn:         string | null;
  type:        string;
  number:      string | null;
  name:        string;
  org:         string | null;
  location:    string | null;
  method:      string | null;
  category:    string | null;
  notice_date: string | null;
  bid_date:    string | null;
  price:       string | null;
  detail_url:  string | null;
  lat:         number | null;
  lon:         number | null;
  fetched_at:  string;
  updated_at:  string;
};
