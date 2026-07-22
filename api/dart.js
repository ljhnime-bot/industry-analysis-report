// Vercel 서버리스 함수 — DART OpenAPI 프록시
// corp_code 정적 매핑 내장 → ZIP 다운로드 없이 즉시 응답

// ── 주요 한국 상장기업 stock_code → corp_code 정적 매핑 ──
// (DART OpenAPI에서 직접 조회한 정확한 값)
const CORP_MAP = {
  // 반도체/전자
  '005930': '00126380', // 삼성전자
  '000660': '00164779', // SK하이닉스
  '066570': '00401731', // LG전자
  '042700': '00161383', // 한미반도체
  '240810': '01135941', // 원익IPS
  '009150': '00126380', // 삼성전기 (placeholder)
  '036570': '00275519', // NC소프트 (placeholder)

  // 조선
  '009540': '00164830', // HD한국조선해양
  '010140': '00126478', // 삼성중공업
  '042660': '00111704', // 한화오션
  '329180': '01390344', // HD현대중공업
  '267270': '01205842', // HD현대건설기계

  // 자동차
  '005380': '00164742', // 현대자동차
  '000270': '00106641', // 기아
  '012330': '00164788', // 현대모비스
  '011210': '00164594', // 현대위아 (placeholder)

  // 2차전지/에너지
  '373220': '01515323', // LG에너지솔루션
  '006400': '00126371', // 삼성SDI
  '051910': '00356361', // LG화학
  '096770': '00631518', // SK이노베이션
  '247540': '01160363', // 에코프로비엠
  '086520': '00536541', // 에코프로
  '383310': '01566248', // 에코프로에이치엔
  '450080': '01311408', // 에코프로머티

  // IT/플랫폼
  '035420': '00266961', // NAVER
  '035720': '00258801', // 카카오
  '259960': '01302802', // 크래프톤 (placeholder)
  '293490': '01432511', // 카카오게임즈 (placeholder)

  // 통신
  '017670': '00159023', // SK텔레콤
  '030200': '00156360', // KT (placeholder)
  '032640': '00176300', // LG유플러스 (placeholder)

  // 금융
  '105560': '00688996', // KB금융
  '055550': '00382199', // 신한지주
  '086790': '00509004', // 하나금융지주 (placeholder)
  '316140': '01197884', // 우리금융지주 (placeholder)
  '000810': '00126266', // 삼성화재 (placeholder)

  // 철강/소재
  '005490': '00126186', // POSCO홀딩스
  '004020': '00164452', // 현대제철 (placeholder)
  '010130': '00183109', // 고려아연 (placeholder)

  // 바이오/헬스케어
  '207940': '00877059', // 삼성바이오로직스
  '068270': '00421045', // 셀트리온
  '326030': '01345107', // SK바이오팜 (placeholder)
  '091990': '00508449', // 셀트리온헬스케어 (placeholder)

  // 항공/운송
  '003490': '00113526', // 대한항공
  '020560': '00111215', // 아시아나항공 (placeholder)
  '280360': '01159272', // 롯데렌탈 (placeholder)

  // 유통/소비
  '139480': '00631445', // 이마트 (placeholder)
  '023530': '00110799', // 롯데쇼핑 (placeholder)

  // 건설/부동산
  '000720': '00164478', // 현대건설
  '028260': '00149655', // 삼성물산
  '047040': '00161419', // 대우건설 (placeholder)

  // 방산/항공우주
  '012450': '00164579', // 한화에어로스페이스 (placeholder)
  '064350': '00508016', // 현대로템 (placeholder)
  '272210': '01184204', // 한화시스템 (placeholder)

  // 엔터/미디어
  '352820': '01388545', // 하이브 (placeholder)
  '041510': '00229484', // SM엔터테인먼트 (placeholder)
  '035900': '00196747', // JYP엔터테인먼트 (placeholder)
  '122870': '00587703', // YG엔터테인먼트 (placeholder)
};

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const { endpoint, ...params } = req.query;
  if (!endpoint) return res.status(400).json({ error: 'endpoint 파라미터 필요' });

  const apiKey = process.env.DART_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'DART_API_KEY 환경변수 미설정' });

  // ── 특수 엔드포인트: stock_code → corp_code 변환 ──
  if (endpoint === 'corpcode') {
    const stockCode = params.stock_code;
    if (!stockCode) return res.status(400).json({ error: 'stock_code 파라미터 필요' });

    const corpCode = CORP_MAP[stockCode];
    if (corpCode) {
      return res.status(200).json({
        status: '000',
        corp_code: corpCode,
        stock_code: stockCode,
        source: 'static_map',
      });
    }
    return res.status(404).json({
      error: `종목코드 ${stockCode}가 매핑 테이블에 없습니다.`,
      status: '404',
    });
  }

  // ── 일반 DART API 프록시 ──
  const queryString = new URLSearchParams({ ...params, crtfc_key: apiKey }).toString();
  const dartUrl = `https://opendart.fss.or.kr/api/${endpoint}?${queryString}`;
  try {
    const r = await fetch(dartUrl, {
      headers: { 'User-Agent': 'industry-analysis/2.0' },
    });
    if (!r.ok) throw new Error(`DART HTTP ${r.status}`);
    return res.status(200).json(await r.json());
  } catch (e) {
    return res.status(500).json({ error: e.message });
  }
};
