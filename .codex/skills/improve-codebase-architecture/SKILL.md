---
name: improve-codebase-architecture
description: 코드베이스에서 깊이를 더할 기회를 찾고, 시각적 HTML 보고서로 제시한 뒤, 선택한 항목을 함께 깊게 검토합니다.
disable-model-invocation: true
---

# 코드베이스 아키텍처 개선

아키텍처상의 마찰을 드러내고 **깊이를 더할 기회**를 제안한다. 즉, 얕은 module을 깊은 module로 바꾸는 리팩터링을 찾는다. 목표는 테스트 용이성과 AI가 탐색하기 쉬운 구조다.

이 명령은 프로젝트의 도메인 모델을 바탕으로 하며, 공유된 설계 어휘 위에 세워진다.

- 아키텍처 어휘(**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**)와 원칙(삭제 테스트, "interface가 테스트 표면이다", "adapter 하나는 가설적 seam, 둘은 실제 seam")을 위해 `/codebase-design` 스킬을 실행한다. 모든 제안에서 이 용어를 정확히 사용한다. "component", "service", "API", "boundary" 같은 표현으로 흐르지 않는다.
- `CONTEXT.md`의 도메인 언어는 좋은 seam에 이름을 붙여 준다. `docs/adr/`의 ADR은 이 명령이 다시 논쟁하지 말아야 할 결정을 기록한다.

## 절차

### 1. 탐색

먼저 프로젝트의 도메인 용어집(`CONTEXT.md`)과 변경 영역에 관련된 ADR을 읽는다.

그다음 Agent 도구를 `subagent_type=Explore`로 사용해 코드베이스를 살핀다. 딱딱한 휴리스틱을 따르지 말고, 자연스럽게 탐색하면서 마찰을 느끼는 지점을 기록한다.

- 하나의 개념을 이해하기 위해 여러 작은 module 사이를 계속 오가야 하는 곳은 어디인가?
- 어떤 module이 **shallow**한가? 즉, interface가 implementation만큼 복잡한 곳은 어디인가?
- 테스트 가능성만을 위해 순수 함수가 추출되었지만, 실제 버그는 그 함수가 호출되는 방식에 숨어 있는 곳은 어디인가(**locality**가 없는 곳)?
- 강하게 결합된 module들이 seam을 넘어 새는 곳은 어디인가?
- 코드베이스에서 테스트되지 않았거나, 현재 interface를 통해 테스트하기 어려운 부분은 어디인가?

shallow하다고 의심되는 대상에는 **삭제 테스트**를 적용한다. 이것을 삭제하면 복잡도가 한곳에 모이는가, 아니면 그저 다른 곳으로 옮겨질 뿐인가? "예, 한곳에 모인다"가 원하는 신호다.

### 2. 후보를 HTML 보고서로 제시

저장소에 아무것도 남기지 않도록 OS 임시 디렉터리에 독립 실행형 HTML 파일을 작성한다. 임시 디렉터리는 `$TMPDIR`에서 확인하고, 없으면 `/tmp`(Windows에서는 `%TEMP%`)를 사용한다. 매 실행마다 새 파일이 생기도록 `<tmpdir>/architecture-review-<timestamp>.html`에 작성한다. 사용자가 볼 수 있게 파일을 연다. Linux에서는 `xdg-open <path>`, macOS에서는 `open <path>`, Windows에서는 `start <path>`를 사용한다. 그리고 절대 경로를 알려 준다.

보고서는 레이아웃과 스타일링에 **CDN을 통한 Tailwind**를 사용하고, 그래프/흐름/시퀀스가 구조를 안정적으로 전달하는 다이어그램에는 **CDN을 통한 Mermaid**를 사용한다. Mermaid와 직접 만든 CSS/SVG 시각 요소를 섞어 쓴다. 관계가 그래프 형태일 때(호출 그래프, 의존성, 시퀀스)는 Mermaid를 사용하고, 더 편집적인 표현이 필요할 때(질량 다이어그램, 단면도, 접힘 애니메이션)는 직접 만든 div/SVG를 사용한다. 각 후보에는 **전/후 시각화**를 넣는다. 시각적으로 보여 준다.

각 후보는 다음 항목을 담은 카드로 렌더링한다.

- **Files** - 관련된 파일/module
- **Problem** - 현재 아키텍처가 왜 마찰을 일으키는지
- **Solution** - 무엇이 바뀌는지 쉬운 문장으로 설명
- **Benefits** - locality와 leverage 관점의 이점, 그리고 테스트가 어떻게 좋아지는지
- **Before / After diagram** - shallowness와 deepening을 나란히 보여 주는 직접 그린 다이어그램
- **Recommendation strength** - `Strong`, `Worth exploring`, `Speculative` 중 하나를 배지로 렌더링

보고서 끝에는 **Top recommendation** 섹션을 둔다. 어떤 후보를 먼저 다룰지와 그 이유를 적는다.

**도메인에는 `CONTEXT.md`의 어휘를, 아키텍처에는 `/codebase-design`의 어휘를 사용한다.** `CONTEXT.md`가 "Order"를 정의한다면 "the Order intake module"이라고 말한다. "the FooBarHandler"나 "the Order service"라고 하지 않는다.

**ADR 충돌**: 후보가 기존 ADR과 모순된다면, 그 ADR을 다시 열어 볼 만큼 실제 마찰이 충분할 때만 제시한다. 카드 안에 명확히 표시한다. 예: 경고 콜아웃 _"ADR-0007과 모순되지만, ... 때문에 다시 열어 볼 가치가 있음"_. ADR이 금지하는 모든 이론적 리팩터링을 나열하지 않는다.

전체 HTML 스캐폴드, 다이어그램 패턴, 스타일 지침은 [HTML-REPORT.md](HTML-REPORT.md)를 참고한다.

아직 interface를 제안하지 않는다. 파일을 작성한 뒤 사용자에게 "어떤 후보를 살펴볼까요?"라고 묻는다.

### 3. 심층 검토 루프

사용자가 후보를 고르면 `/grilling` 스킬을 실행해 함께 설계 트리를 따라간다. 제약, 의존성, 깊어진 module의 형태, seam 뒤에 놓일 것, 유지될 테스트를 검토한다.

결정이 선명해지는 즉시 부수 효과를 반영한다. 진행하면서 도메인 모델을 최신으로 유지하기 위해 `/domain-modeling` 스킬을 실행한다.

- **`CONTEXT.md`에 없는 개념으로 깊어진 module에 이름을 붙이는가?** 그 용어를 `CONTEXT.md`에 추가한다. 파일이 없다면 필요할 때 생성한다.
- **대화 중 흐릿한 용어를 더 선명하게 다듬었는가?** 그 자리에서 `CONTEXT.md`를 갱신한다.
- **사용자가 구조적으로 중요한 이유로 후보를 거절했는가?** 다음처럼 ADR 작성을 제안한다. _"향후 아키텍처 리뷰에서 다시 제안하지 않도록 이 결정을 ADR로 기록할까요?"_ 같은 제안을 피하기 위해 미래의 탐색자가 실제로 알아야 할 이유일 때만 제안한다. 일시적인 이유("지금은 할 가치가 없음")나 자명한 이유는 건너뛴다.
- **깊어진 module의 대안 interface를 탐색하고 싶은가?** `/codebase-design` 스킬을 실행하고 design-it-twice 병렬 서브에이전트 패턴을 사용한다.
