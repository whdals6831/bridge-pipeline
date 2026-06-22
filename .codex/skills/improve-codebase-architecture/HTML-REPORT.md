# HTML 보고서 형식

아키텍처 리뷰는 OS 임시 디렉터리에 하나의 독립 실행형 HTML 파일로 렌더링한다. Tailwind와 Mermaid는 모두 CDN에서 가져온다. Mermaid는 그래프 형태의 다이어그램을 안정적으로 처리하고, 직접 만든 div와 인라인 SVG는 더 편집적인 시각 표현(질량 다이어그램, 단면도)을 담당한다. 둘을 섞어 쓴다. 모든 것을 Mermaid에 의존하면 금방 일반적인 보고서처럼 보인다.

## 스캐폴드

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Architecture review — {{repo name}}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="module">
      import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
      mermaid.initialize({ startOnLoad: true, theme: "neutral", securityLevel: "loose" });
    </script>
    <style>
      /* small custom layer for things Tailwind doesn't cover cleanly:
         dashed seam lines, hand-drawn-feeling arrow heads, etc. */
      .seam { stroke-dasharray: 4 4; }
      .leak { stroke: #dc2626; }
      .deep { background: linear-gradient(135deg, #0f172a, #1e293b); }
    </style>
  </head>
  <body class="bg-stone-50 text-slate-900 font-sans">
    <main class="max-w-5xl mx-auto px-6 py-12 space-y-12">
      <header>...</header>
      <section id="candidates" class="space-y-10">...</section>
      <section id="top-recommendation">...</section>
    </main>
  </body>
</html>
```

## 헤더

저장소 이름, 날짜, 간결한 범례를 넣는다. 실선 상자 = module, 점선 = seam, 빨간 화살표 = 누수, 두꺼운 어두운 상자 = deep module. 소개 문단은 넣지 않는다. 바로 후보로 들어간다.

## 후보 카드

핵심은 다이어그램이 전달한다. 글은 적고, 평이하며, `/codebase-design` 스킬의 용어집 표현을 자연스럽게 사용한다.

각 후보는 하나의 `<article>`이다.

- **Title** - 짧게 작성하고 deepening의 이름을 붙인다. 예: "Collapse the Order intake pipeline".
- **Badge row** - 추천 강도(`Strong` = emerald, `Worth exploring` = amber, `Speculative` = slate)와 의존성 범주 태그(`in-process`, `local-substitutable`, `ports & adapters`, `mock`)를 함께 둔다.
- **Files** - 고정폭 목록, `font-mono text-sm`.
- **Before / After diagram** - 중심 요소다. 두 열을 나란히 둔다. 아래 패턴을 참고한다.
- **Problem** - 한 문장. 무엇이 아픈지.
- **Solution** - 한 문장. 무엇이 바뀌는지.
- **Wins** - 각 bullet은 6단어 이하. 예: "Tests hit one interface", "Pricing logic stops leaking", "Delete 4 shallow wrappers".
- **ADR callout**(해당하는 경우) - amber 톤 상자에 한 줄로 작성한다.

설명 문단은 넣지 않는다. 다이어그램을 이해하는 데 문단이 필요하다면 다이어그램을 다시 그린다.

## 다이어그램 패턴

후보에 맞는 패턴을 고른다. 섞어서 사용한다. 모든 다이어그램이 똑같아 보이게 만들지 않는다. 다양성도 목적의 일부다.

### Mermaid 그래프(의존성 / 호출 흐름의 기본 도구)

요점이 "X가 Y를 호출하고 Y가 Z를 호출하는데, 이 복잡함을 보라"일 때 Mermaid `flowchart`나 `graph`를 사용한다. 뜬금없이 끼워 넣은 것처럼 보이지 않도록 Tailwind 스타일 카드로 감싼다. `classDef`로 leakage edge는 빨간색, deep module은 어두운 색으로 스타일링한다. "before: 왕복 6번, after: 1번" 같은 경우에는 시퀀스 다이어그램이 잘 맞는다.

```html
<div class="rounded-lg border border-slate-200 bg-white p-4">
  <pre class="mermaid">
    flowchart LR
      A[OrderHandler] --> B[OrderValidator]
      B --> C[OrderRepo]
      C -.leak.-> D[PricingClient]
      classDef leak stroke:#dc2626,stroke-width:2px;
      class C,D leak
  </pre>
</div>
```

### 직접 만든 상자와 화살표(Mermaid 레이아웃이 맞지 않을 때)

module은 테두리와 라벨이 있는 `<div>`로 표현한다. 화살표는 relative container 위에 absolute로 배치한 인라인 SVG `<line>` 또는 `<path>` 요소로 표현한다. "after" 다이어그램이 회색 처리된 내부를 가진, 두꺼운 테두리의 deep module 하나처럼 느껴져야 할 때 사용한다. Mermaid로는 그 무게감을 제대로 렌더링하기 어렵다.

### 단면도(layered shallowness에 적합)

가로 밴드(`h-12 border-l-4`)를 쌓아 호출이 통과하는 layer들을 보여 준다. Before: 각각 아무 일도 하지 않는 얇은 layer 6개. After: 통합된 책임으로 라벨링된 두꺼운 밴드 1개.

### 질량 다이어그램("interface가 implementation만큼 넓음"을 보여 주기에 적합)

module마다 직사각형 두 개를 둔다. 하나는 interface 표면적, 하나는 implementation을 나타낸다. Before: interface 직사각형이 implementation 직사각형만큼 거의 높다(shallow). After: interface 직사각형은 짧고, implementation 직사각형은 높다(deep).

### 호출 그래프 접기

Before: 함수 호출 트리를 중첩 상자로 렌더링한다. After: 같은 트리를 하나의 상자로 접고, 이제 내부가 된 호출은 그 안에 흐리게 표시한다.

## 스타일 지침

- 기업 대시보드가 아니라 편집물에 가깝게 만든다. 여백을 넉넉히 둔다. 제목에는 serif를 선택적으로 쓸 수 있다(`font-serif`는 stone/slate와 잘 어울린다).
- 색은 아껴 쓴다. accent 하나(emerald 또는 indigo), leakage용 red, warning용 amber 정도로 제한한다.
- before/after가 스크롤 없이 나란히 편하게 보이도록 다이어그램 높이는 약 320px로 유지한다.
- 다이어그램 안의 module 라벨에는 `text-xs uppercase tracking-wider`를 사용한다. UI가 아니라 도식처럼 읽혀야 한다.
- 스크립트는 Tailwind CDN과 Mermaid ESM import뿐이다. 보고서는 그 외에는 정적이다. 앱 코드도 없고, Mermaid 자체 렌더링 외의 상호작용도 없다.

## Top recommendation 섹션

더 큰 카드 하나를 둔다. 후보 이름, 이유 한 문장, 해당 카드로 가는 anchor link. 그것이면 충분하다.

## 톤

쉬운 문장으로 간결하게 쓴다. 단, 아키텍처 명사와 동사는 `/codebase-design` 스킬에서 그대로 가져온다. 간결함을 핑계로 용어가 흔들리면 안 된다.

**정확히 사용할 것:** module, interface, implementation, depth, deep, shallow, seam, adapter, leverage, locality.

**대체어로 쓰지 말 것:** component, service, unit(module의 의미로) · API, signature(interface의 의미로) · boundary(seam의 의미로) · layer, wrapper(module을 뜻할 때).

**스타일에 맞는 표현:**

- "Order intake module is shallow — interface nearly matches the implementation."
- "Pricing leaks across the seam."
- "Deepen: one interface, one place to test."
- "Two adapters justify the seam: HTTP in prod, in-memory in tests."

**Wins bullet**은 용어집 표현으로 이점을 말한다. *"locality: bugs concentrate in one module"*, *"leverage: one interface, N call sites"*, *"interface shrinks; implementation absorbs the wrappers"*처럼 쓴다. *"easier to maintain"* 또는 *"cleaner code"*라고 쓰지 않는다. 그런 표현은 용어집에 없고, 들어갈 자격을 얻지 못한다.

애매한 완충 표현이나 서두를 넣지 않는다. "it's worth noting that..." 같은 문구도 쓰지 않는다. 문장이 bullet이 될 수 있다면 bullet로 만든다. bullet을 지울 수 있다면 지운다. 어떤 용어가 `/codebase-design` 용어집에 없다면, 새로 만들기 전에 용어집에 있는 표현을 먼저 찾는다.
