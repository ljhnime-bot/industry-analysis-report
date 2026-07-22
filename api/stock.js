// Vercel 서버리스 함수 — 주가 프록시
// 네이버금융 → Yahoo Finance 순으로 서버에서 직접 호출 (CORS/403 없음)
module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const { ticker } = req.query;
  if (!ticker) return res.status(400).json({ error: 'ticker 파라미터 필요' });

  // ① 네이버 금융 (Vercel 서버에서 호출 — 403 없음)
  try {
    const naverUrl = `https://m.stock.naver.com/api/stock/${ticker}/basic`;
    const r = await fetch(naverUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',
        'Accept': 'application/json',
        'Referer': 'https://m.stock.naver.com/',
      }
    });
    if (r.ok) {
      const d = await r.json();
      const price = parseInt((d.closePrice || '0').replace(/,/g, ''));
      if (price > 0) {
        const diff   = parseInt((d.compareToPreviousPrice?.value || '0').replace(/,/g, ''));
        const change = parseFloat((d.fluctuationsRatio || '0').replace(/[+]/g, ''));
        return res.status(200).json({
          price, prevClose: price - diff,
          change: change.toFixed(2), currency: 'KRW',
          week52High: parseInt((d.highPrice || '0').replace(/,/g, '')),
          week52Low:  parseInt((d.lowPrice  || '0').replace(/,/g, '')),
          source: '네이버금융', ticker,
        });
      }
    }
  } catch(_) {}

  // ② Yahoo Finance 폴백
  const symbol = ticker.includes('.') ? ticker : `${ticker}.KS`;
  try {
    const yahooUrl = `https://query2.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d&range=5d`;
    const r = await fetch(yahooUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
      }
    });
    if (r.ok) {
      const json = await r.json();
      const meta = json.chart?.result?.[0]?.meta;
      if (meta?.regularMarketPrice) {
        const prev = meta.previousClose || meta.chartPreviousClose || meta.regularMarketPrice;
        return res.status(200).json({
          price:     Math.round(meta.regularMarketPrice),
          prevClose: Math.round(prev),
          change:    ((meta.regularMarketPrice - prev) / prev * 100).toFixed(2),
          currency:  meta.currency || 'KRW',
          week52High: Math.round(meta.fiftyTwoWeekHigh || 0),
          week52Low:  Math.round(meta.fiftyTwoWeekLow  || 0),
          source: 'Yahoo Finance', ticker,
        });
      }
    }
  } catch(_) {}

  return res.status(500).json({ error: '주가 수집 실패', ticker });
};
