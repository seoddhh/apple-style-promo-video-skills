# 모션 레시피 — UI · 데이터 · 전환

타이포 무브는 [typography-playbook.md](typography-playbook.md)에 있다. 이 문서는 제품 UI를 움직이는 레시피다. 모든 레시피는 장면의 `draw(lt, t)` 안에서 호출한다. 헬퍼(`p`, `eo`, `eio`, `spring`, `lerp`, `mv`)는 template.html에 들어 있다.

목차: 타이밍 · UI 인터랙션 · 아이콘 모션 · 데이터 · 연속 변환 · 전환 · 목업 연출 · 저자극 버전

## 타이밍

- 등장은 0.5~0.9초, 퇴장은 0.3~0.4초. 여러 요소는 0.1~0.18초 간격으로 stagger한다.
- linear 이징은 쓰지 않는다 (타이핑 커서만 예외).
- **결과가 나온 뒤에는 최소 0.8초 머문다.** 결과를 보여주려고 만든 영상이다.
- 움직임은 이유가 있을 때만 준다. "이게 저게 됐다"(인과)나 "여기서 저기로"(위치)를 말하지 않는 이동은 제자리 페이드로 바꾼다.
- 방향을 일관되게 유지한다. 오른쪽으로 진행하는 흐름이면 다음 요소도 오른쪽에서 들어온다.

## UI 인터랙션 (손가락은 그리지 않는다)

```js
// 타이핑: 한글은 초당 12~16자, 커서는 Math.floor(lt*2)%2
function typeText(el,lt,start,text,cps=14){const n=Math.floor(Math.max(0,lt-start)*cps);
  el.textContent=text.slice(0,n); el.dataset.caret=(n<text.length||Math.floor(lt*2)%2)?'1':'0';}
// 탭 리플: 200px 원(border 4px) 하나를 재사용
function ripple(el,lt,st,cx,cy,maxR=120,dur=.6){const k=p(lt,st,st+dur);
  el.style.transform=`translate(${cx-100}px,${cy-100}px) scale(${eo(k)*maxR/100})`;
  el.style.opacity=(k>0&&k<1)?1-k:0;}
// 버튼 탭: 눌림 → 채움 → 상태 변화
const tp=p(lt,st,st+.45); btn.style.transform=`scale(${1-Math.sin(Math.min(tp/.4,1)*Math.PI)*.08})`;
fill.style.transform=`scaleX(${eo(p(lt,st+.05,st+.4))})`;   // transform-origin:left
// 처리 중: 점 3개가 sin(lt*10 - i*.9)로 위아래, 또는 스켈레톤 줄에 shimmer(backgroundPosition을 lt로). 0.4~0.6초만
// 리스트 채움: 결과 항목이 .12초 간격으로 translateY(24→0) + opacity
// 스크롤: 내부 컨테이너 translateY를 eio로 구간 이동 (등속 스크롤 금지)
// 드래그 앤 드롭: 카드가 곡선 경로(lerp + sin 아치)로 이동 → 드롭존 테두리 포인트 컬러 → 착지 시 spring
// 체크: SVG path에 pathLength=1, strokeDashoffset = 1 - eo(k)
```

- 헤드라인은 "무엇을 했는지"가 아니라 "무엇을 얻었는지"를 말한다. UI가 행동을 보여주니 글자는 결과를 말한다.
- 로딩은 짧게 보여준다. 길면 느린 제품처럼 보인다.

## 아이콘 모션 (애플 아이콘 애니메이션 문법)

아이콘 하나에 효과 한 종류만, 화면 하나에 한 번만 쓴다.

| 효과 | 뜻 | 구현 (k = 0~1) |
|---|---|---|
| Bounce | 동작이 일어났다 | `scale(1 - sin(k*π)*.18)` 0.35초, 한 번 |
| Replace | 상태가 바뀌었다 (＋→✓) | 이전 아이콘 scale 1→0 + 페이드, 0.12초 뒤 새 아이콘 spring 0→1 |
| Draw On | 진행·완료 (체크, 경로) | `strokeDashoffset = 1 - eo(k)` |
| Pulse | 진행 중 (녹음, 분석) | opacity `.55 + .45*cos(lt*4)` |
| Variable color | 단계적 진행 | 레이어 n개를 순서대로 opacity .3→1 |

## 데이터

```js
// 막대: scaleY(transform-origin:bottom), 막대마다 .08초 stagger
// 선 차트: SVG path에 pathLength=1, strokeDasharray=1, strokeDashoffset=1-eo(k)
// 링: stroke-dasharray로 호 길이를 k에 비례
// 비교 막대: 두 막대가 같이 자라다 k>.5부터 제품 쪽만 계속 자라고, 끝나면 포인트 컬러
// 연결선 + 패킷: 선은 dashoffset, 점은 path.getPointAtLength(len*k) (len은 measure에서 저장)
```

- 차트 위에는 축 설명이 아니라 **결론 한 문장**을 둔다 ("주말 오후 3시가 가장 붐벼요").
- 숫자 하나로 말할 수 있으면 차트 대신 숫자 히어로(typography-playbook ⑩)를 쓴다. 애플은 차트보다 큰 숫자를 쓴다.

## 연속 변환 — 퀄리티를 가장 크게 좌우한다

요소를 지우고 새 요소를 띄우는 대신, **같은 요소가 모양을 바꾸며 다음 자리로 이동**하게 한다. 그러면 "이 입력이 이 결과가 됐다"는 인과가 보인다.

예: 헤드라인 속 키워드 → 칩으로 떨어져 나옴 → 결과 카드의 빈 자리(slot)에 착지 → 다음 장면 결과에도 같은 칩이 붙어 있음.

```js
// slot 기법: 카드 안에 visibility:hidden인 자리 요소를 두고 measure()에서 좌표를 잰다.
// 실제 칩은 카드 밖 absolute 레이어에서 translate로 이동한다.
// measure() 안에서는 부모 transform을 'none'으로 둔 뒤 getBoundingClientRect()
x=lerp(a.x,b.x,eio(k)); y=lerp(a.y,b.y,eio(k));
// 크기·모양: fontSize, width, height, borderRadius, 배경 opacity를 같은 k로 lerp (글자 → 칩, 카드 → 풀스크린)
```

## 전환

| 전환 | 방법 | 쓰는 곳 |
|---|---|---|
| 디졸브 (기본) | 장면에 `overlap: .4` | 대부분 |
| 하드컷 | `overlap` 없음 | 템포 컷, 정적 비트 앞뒤, 리빌 |
| 정적 → 리빌 | 빈 장면 0.3~0.6초 + 하드컷 | 제품명 등장 (typography-playbook ⑬) |
| 글자 속 줌 | `zoomThrough` → 하드컷 | 다크 ↔ 라이트 전환 (⑭) |
| UI 줌 | 카드가 scale로 커져 풀스크린 → 그 안 UI가 다음 장면 | 기능 월 → 기능 상세 |
| 자리 비켜주기 | 이전 결과를 `translateX(-440px) scale(.76)`로 밀어내고 빈자리에 다음 요소 | 이전 결과가 다음 기능의 재료일 때 |
| 원형 와이프 | `clip-path: circle(0→1200px at 중심)`, eio 0.8초 | 배경색이 바뀔 때 |

- 매치컷 계열(UI 줌, 자리 비켜주기, 와이프)은 영상 하나에 2종류까지만 쓴다. 두 장면을 직접 제어하려면 `tr:'manual'`을 준다.
- 디졸브되어 들어오는 장면의 요소는 `lt ≥ overlap`부터 등장시킨다.

## 목업 연출

- 등장: 부모에 `perspective:2000px`, `rotateY(-10deg→0) rotateX(5deg→0)` + translateY 60px → 0, eo 1초.
- 튀어나오기: 화면 속 핵심 결과 하나를 복제해 목업 밖으로 띄운다 (scale 1.08 + 그림자 강화). 영상에서 한 번만 쓴다.
- 줌인: 목업 전체를 보여준 다음 핵심 영역으로 scale 1→1.8, eio 1초. 작은 UI를 읽히게 하는 가장 쉬운 방법이다.
- 캡처를 여러 장 받으면 목업은 고정해 두고 화면만 디졸브나 가로 슬라이드로 바꾼다.
- 탭 위치는 원 하나(ripple)로 알린다. 손가락은 그리지 않는다.

## 저자극 버전 (요청이 있을 때만)

```bash
python3 render.py promo.html --motion reduced --out promo_reduced.mp4
```

`REDUCED` 플래그가 켜지면 template의 헬퍼가 이동·블러·스프링을 끄고 페이드만 남긴다. 직접 쓴 장면 코드에서는 이동량을 `mv(값)`으로 감싼다.
