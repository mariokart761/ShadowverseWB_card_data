// supabase/functions/deck-crawler/index.ts
// ------------------------------------------------------------
// Shadowverse 牌組資訊擷取器（Supabase Edge Function / Deno）
// 雙模式：URL / Deck Code，含舊網址前處理
// - URL 模式：直接抓取會回傳 JSON 的網址；若偵測到
//   https://shadowverse-wb.com/<lang>/deck/detail/?hash=...
//   會自動轉為
//   https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail?hash=...&lang=<lang>
// - Deck Code 模式：POST 到 https://shadowverse-wb.com/web/DeckCode/getDeck
//   payload: { deck_code: "XXXX" }
// - 支援 GET 與 POST 請求，皆回傳 { ok, data } 或 { ok:false, error }
// - 內建 CORS 與 OPTIONS 預檢
// ------------------------------------------------------------

export type DeckData = {
    total_red_ether: number;
    num_follower: number;
    num_spell: number;
    num_amulet: number;
    mana_curve: Record<string, number>;
    battle_format: number;
    class_id: number;
    sub_class_id: number | null;
    sort_card_id_list: Array<number | string>;
    deck_card_num: Record<string, number>;
  };
  
  const DEFAULT_DECK: DeckData = {
    total_red_ether: 0,
    num_follower: 0,
    num_spell: 0,
    num_amulet: 0,
    mana_curve: {},
    battle_format: 2,
    class_id: 5,
    sub_class_id: null,
    sort_card_id_list: [],
    deck_card_num: {},
  };
  
  const CANDIDATE_ROOT_KEYS = [
    "data",
    "result",
    "deckDetail",
    "deck",
    "payload",
  ] as const;
  
  const GET_DECK_ENDPOINT =
    "https://shadowverse-wb.com/web/DeckCode/getDeck" as const;
  
  const corsHeaders: Record<string, string> = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers":
      "authorization, x-client-info, apikey, content-type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Content-Type": "application/json; charset=utf-8",
  };
  
  function jsonResponse(body: unknown, status = 200) {
    return new Response(JSON.stringify(body), { status, headers: corsHeaders });
  }
  
  function dig(obj: any, key: string): unknown {
    if (obj && typeof obj === "object" && key in obj) return obj[key];
    for (const rk of CANDIDATE_ROOT_KEYS) {
      const sub = obj?.[rk as keyof typeof obj];
      if (sub && typeof sub === "object" && key in sub) return (sub as any)[key];
    }
    return undefined;
  }
  
  function formatDeckData(raw: any): DeckData {
    return {
      total_red_ether:
        (dig(raw, "total_red_ether") as number) ?? DEFAULT_DECK.total_red_ether,
      num_follower: (dig(raw, "num_follower") as number) ?? DEFAULT_DECK.num_follower,
      num_spell: (dig(raw, "num_spell") as number) ?? DEFAULT_DECK.num_spell,
      num_amulet: (dig(raw, "num_amulet") as number) ?? DEFAULT_DECK.num_amulet,
      mana_curve:
        (dig(raw, "mana_curve") as Record<string, number>) ?? DEFAULT_DECK.mana_curve,
      battle_format: (dig(raw, "battle_format") as number) ?? DEFAULT_DECK.battle_format,
      class_id: (dig(raw, "class_id") as number) ?? DEFAULT_DECK.class_id,
      sub_class_id:
        (dig(raw, "sub_class_id") as number | null) ?? DEFAULT_DECK.sub_class_id,
      sort_card_id_list:
        (dig(raw, "sort_card_id_list") as Array<number | string>) ??
        DEFAULT_DECK.sort_card_id_list,
      deck_card_num:
        (dig(raw, "deck_card_num") as Record<string, number>) ??
        DEFAULT_DECK.deck_card_num,
    };
  }
  
  async function parseJsonResponse(resp: Response): Promise<any> {
    if (!resp.ok) {
      const text = await resp.text().catch(() => "");
      throw new Error(`HTTP ${resp.status} ${resp.statusText}${text ? ` - ${text}` : ""}`);
    }
    try {
      return await resp.json();
    } catch {
      const text = await resp.text();
      try {
        return JSON.parse(text);
      } catch (e) {
        throw new Error(`內容不是合法 JSON：${(e as Error).message}`);
      }
    }
  }
  
  async function fetchJsonViaUrl(url: string, ua?: string): Promise<any> {
    const headers = new Headers();
    if (ua) headers.set("User-Agent", ua);
    const resp = await fetch(url, { headers });
    const obj = await parseJsonResponse(resp);
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) {
      throw new Error("最外層 JSON 不是物件（dict），不符合預期");
    }
    return obj;
  }
  
  async function fetchJsonViaDeckCode(deckCode: string, ua?: string): Promise<any> {
    const headers = new Headers({ "Content-Type": "application/json; charset=utf-8" });
    if (ua) headers.set("User-Agent", ua);
    const resp = await fetch(GET_DECK_ENDPOINT, {
      method: "POST",
      headers,
      body: JSON.stringify({ deck_code: deckCode }),
    });
    const obj = await parseJsonResponse(resp);
    if (!obj || typeof obj !== "object" || Array.isArray(obj)) {
      throw new Error("最外層 JSON 不是物件（dict），不符合預期");
    }
    return obj;
  }
  
  function normalizeDeckUrlIfNeeded(rawUrl: string): { url: string; detectedLang?: string | null } {
    let detectedLang: string | null = null;
    let url: URL;
    try {
      url = new URL(rawUrl);
    } catch {
      // 若缺 scheme，預設補 https
      url = new URL(`https://${rawUrl}`);
    }
  
    const host = url.hostname.toLowerCase();
    const path = url.pathname.toLowerCase();
    if (!host.endsWith("shadowverse-wb.com")) {
      return { url: url.toString(), detectedLang };
    }
  
    const hashVal = url.searchParams.get("hash");
    const segs = path.split("/").filter(Boolean); // 去空片段
  
    // 形態一：/<lang>/deck/detail(/)
    if (
      segs.length >= 3 &&
      segs[1] === "deck" &&
      segs[2].startsWith("detail")
    ) {
      const first = segs[0];
      if (!(["web", "deck", "builder"].includes(first))) {
        detectedLang = first;
      }
    }
  
    // 形態二：/deck/detail(/)（不含語言片段）→ detectedLang 保持 null
    const looksLikeOld =
      (segs.length >= 3 && segs[1] === "deck" && segs[2].startsWith("detail")) ||
      (segs.length >= 2 && segs[0] === "deck" && segs[1].startsWith("detail"));
  
    if (looksLikeOld && hashVal) {
      const newUrl = new URL("https://shadowverse-wb.com/web/DeckBuilder/deckHashDetail");
      newUrl.searchParams.set("hash", hashVal);
      // 若原本帶 lang，沿用；否則用 path 偵測到的語言
      const qLang = url.searchParams.get("lang");
      if (qLang) newUrl.searchParams.set("lang", qLang);
      else if (detectedLang) newUrl.searchParams.set("lang", detectedLang);
      return { url: newUrl.toString(), detectedLang };
    }
  
    return { url: url.toString(), detectedLang };
  }
  
  function addOrUpdateLangQuery(inputUrl: string, lang?: string | null): string {
    if (!lang) return inputUrl;
    const u = new URL(inputUrl);
    u.searchParams.set("lang", String(lang));
    return u.toString();
  }
  
  Deno.serve(async (req: Request) => {
    if (req.method === "OPTIONS") {
      return new Response("ok", { headers: corsHeaders });
    }
  
    try {
      const { searchParams } = new URL(req.url);
      const isJSON = req.headers.get("content-type")?.includes("application/json");
  
      // 支援 GET query 與 POST body 兩種輸入
      let urlParam = searchParams.get("url") ?? undefined;
      let deckCode = searchParams.get("deck_code") ?? searchParams.get("deckCode") ?? undefined;
      let lang = searchParams.get("lang") ?? undefined;
      let ua = searchParams.get("ua") ?? undefined;
  
      if ((req.method === "POST" || req.method === "PUT") && isJSON) {
        const body = await req.json().catch(() => ({} as Record<string, unknown>));
        urlParam = (body?.url as string) ?? urlParam;
        deckCode = (body?.deck_code as string) ?? (body?.deckCode as string) ?? deckCode;
        lang = (body?.lang as string) ?? lang;
        ua = (body?.ua as string) ?? ua;
      }
  
      if (!urlParam && !deckCode) {
        return jsonResponse({ ok: false, error: "請提供 url 或 deck_code 其中之一" }, 400);
      }
  
      if (urlParam && deckCode) {
        return jsonResponse({ ok: false, error: "url 與 deck_code 僅能擇一" }, 400);
      }
  
      // --- URL 模式 ---
      if (urlParam) {
        const { url: normalized, detectedLang } = normalizeDeckUrlIfNeeded(urlParam);
        const finalUrl = addOrUpdateLangQuery(normalized, lang ?? detectedLang ?? undefined);
        const raw = await fetchJsonViaUrl(finalUrl, ua);
        const deck = formatDeckData(raw);
        return jsonResponse({ ok: true, data: deck }, 200);
      }
  
      // --- Deck Code 模式 ---
      if (deckCode) {
        const raw = await fetchJsonViaDeckCode(deckCode, ua);
        const deck = formatDeckData(raw);
        return jsonResponse({ ok: true, data: deck }, 200);
      }
  
      // 正常不會到這裡
      return jsonResponse({ ok: false, error: "未知錯誤" }, 500);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return jsonResponse({ ok: false, error: msg }, 400);
    }
  });
  
  /**
   * --- 使用說明 ---
   *
   * 1) 建立函式目錄（Supabase CLI）：
   *    $ supabase functions new deck-crawler
   *    以此檔案覆蓋 supabase/functions/deck-crawler/index.ts
   *
   * 2) 本地啟動（免驗證）：
   *    $ supabase functions serve deck-crawler --no-verify-jwt
   *
   * 3) 測試：
   *    # URL 模式（新式 URL）
   *    curl -i "http://localhost:54321/functions/v1/deck-crawler?url=https%3A%2F%2Fshadowverse-wb.com%2Fweb%2FDeckBuilder%2FdeckHashDetail%3Fhash%3Dabc%26lang%3Dcht"
   *
   *    # URL 模式（舊式 URL，會自動轉換）
   *    curl -i "http://localhost:54321/functions/v1/deck-crawler?url=https%3A%2F%2Fshadowverse-wb.com%2Fcht%2Fdeck%2Fdetail%2F%3Fhash%3Dabc"
   *
   *    # Deck Code 模式（POST）
   *    curl -i -H 'Content-Type: application/json' \
   *      -d '{"deck_code":"Ab1C"}' \
   *      http://localhost:54321/functions/v1/deck-crawler
   *
   * 4) 部署：
   *    $ supabase functions deploy deck-crawler
   *
   * 5) 雲端測試：
   *    curl -i \
   *      -H "Authorization: Bearer <YOUR_ANON_KEY>" \
   *      -H "apikey: <YOUR_ANON_KEY>" \
   *      "https://<PROJECT-REF>.functions.supabase.co/deck-crawler?deck_code=Ab1C"
   *
   * 備註：
   * - 可選 query/body 欄位：ua（User-Agent）、lang（僅 URL 模式適用；會覆蓋前處理偵測到的語言）
   * - 回傳格式（成功）：{ ok: true, data: DeckData }
   * - 回傳格式（失敗）：{ ok: false, error: string }
   */
  