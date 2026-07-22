# 산업분석 투자 리포트 생성기

증권사 애널리스트 스타일의 **AI 기반 산업분석 투자 리포트 생성기**입니다.
사용자가 국가·산업·커버리지 기업을 입력하면, 실시간 주가와 DART 재무 데이터를 수집한 뒤
LLM(Claude / ChatGPT / Gemini / Perplexity)으로 기관 투자자용 리포트를 자동 생성합니다.

> **매크로분석 → 산업분석 → 기업분석** 3단계로 이어지는 탑다운 분석 흐름을,
> 별도 백엔드 없이 **단일 HTML 파일(바닐라 JS)** 안에서 구현했습니다.

---

## 주요 기능

- **3단계 분석 파이프라인** — 📈 매크로 · 🏭 산업 · 🏢 기업 탭을 전환하며 단계별 리포트를 생성하고,
  앞 단계 결과를 다음 단계 컨텍스트로 연결(체크박스)해 일관된 탑다운 분석을 구성
- **실시간 데이터 수집** — 커버리지 기업별 주가(네이버금융→Yahoo 폴백), DART 연간·분기 재무,
  그리고 매크로 지표(환율·美 국채금리·S&P/나스닥/코스피·VIX·유가·금)를 병렬 수집해 리포트에 주입
  (LLM이 금리·환율을 지어내지 않고 실측값을 사용)
- **멀티 LLM 지원** — Claude / OpenAI / Gemini / Perplexity를 SSE 스트리밍으로 호출, 마크다운을 점진 렌더링
- **분석 프레임워크 내장** — PESTEL · Porter 5 Forces · 가치사슬 · TAM/SAM/SOM · S-Curve · 해자(Moat) · 단위경제성 등
- **애널리스트 산출물** — 투자의견 박스(Bull/Base/Bear 시나리오), Chart.js 차트, 신뢰도 태그
  (`[공시]` `[컨센서스]` `[AI추정]`)와 추정치 비중 경고 배너
- **라이트/다크 테마** — CSS 변수 기반 원클릭 토글 (localStorage 저장)

## 기술 스택

| 구분 | 내용 |
|---|---|
| 프론트엔드 | Vanilla JS (빌드·번들러·프레임워크 없음), 단일 HTML 인라인 |
| 시각화 | Chart.js |
| 마크다운 | marked.js |
| 데이터 | DART Open API(재무·공시), 네이버금융 / Yahoo Finance(주가) |
| LLM | Anthropic · OpenAI · Google · Perplexity API |
| 배포(선택) | Vercel Serverless (`api/dart.js`, `api/stock.js`) — CORS 우회 서버 프록시 |

## 사용법

1. `index.html` 을 브라우저로 직접 엽니다. (빌드 불필요)
2. 사이드바에 사용하려는 **LLM API 키**를 입력합니다. (키는 브라우저에만 저장되며 서버로 전송되지 않음)
3. 재무 데이터를 쓰려면 **DART API 키**를 입력합니다. ([DART 오픈API](https://opendart.fss.or.kr/) 무료 발급)
4. 국가·산업·커버리지 기업을 입력하고 리포트를 생성합니다.

> **CORS 우회**: `file://` 또는 GitHub Pages 환경에서는 `api.allorigins.win` 프록시를 경유하고,
> Vercel 배포 시에는 `api/` 서버리스 함수가 외부 API를 직접 호출합니다.

## 아키텍처 (핵심 흐름)

`generateReport()` 가 3단계 파이프라인의 중심입니다:

1. **STEP 1 — 데이터 수집**: 커버리지 기업별 주가 + DART 재무/공시를 `Promise.all`로 병렬 수집
2. **STEP 2 — LLM 호출**: `BASE_SYSTEM_PROMPT` + 산업 모듈 프롬프트를 조립해 SSE 스트리밍 호출
3. **STEP 3 — 렌더링**: `marked.parse` → 신뢰도 태그 치환 → 투자의견 박스 → 차트 → 추정치 비중 검증

LLM 출력은 특수 마커(`%%CHART%%…`, `%%OPINION%%…`, `[신뢰도 태그]`)를 포함하도록 프롬프트로 강제되고,
클라이언트 파서가 이를 UI 컴포넌트로 변환하는 **프롬프트↔파서 계약** 구조입니다.

## 프로젝트 구조

```
├─ index.html             # 정식 애플리케이션 (단일 파일, ~3,500줄)
├─ api/
│  ├─ dart.js              # DART 프록시 (Vercel Serverless)
│  └─ stock.js             # 주가 프록시 (네이버→Yahoo 폴백)
├─ fetch_dart_financials.py # DART 재무제표 병렬 수집 스크립트
├─ frameworks.md           # 분석 프레임워크 정의
└─ vercel.json             # Vercel 런타임 설정
```

## 보안 참고

- LLM·DART API 키는 **코드에 하드코딩하지 않으며**, 사용자가 UI에서 직접 입력합니다.
- Python 스크립트는 환경변수로 키를 읽습니다: `DART_API_KEY`

---

*본 도구가 생성하는 리포트는 정보 제공 목적이며, 투자 자문 또는 투자 권유가 아닙니다.*
