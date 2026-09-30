# 모션 레시피

모든 레시피는 장면의 `draw(lt, t)` 안에서 호출한다. `lt`는 장면 시작 기준 로컬 시간. 헬퍼(`p`, `eo`, `eio`, `spring`, `lerp`)는 template.html에 들어 있다. 수치는 검증된 기본값이다.

목차: 타이밍 원칙 · 텍스트 · UI 인터랙션 · 데이터·증거 · 연속 변환 · 컷 전환 · 장식(아껴 쓰기)

## 타이밍 원칙
- 컷당 2~4초. 정지 화면은 0.5초를 넘기지 않는다 (단, 헤드라인 읽기 시간은 확보. design-system.md의 읽는 시간 공식).
- 등장 0.5~0.9초, 퇴장 0.3~0.4초. 퇴장이 등장보다 빠르다.
- 여러 요소는 0.1~0.18초 간격 stagger. 동시에 등장시키지 않는다.
- linear 이징은 쓰지 않는다 (예외: 타이핑 커서, 데이터 패킷 이동의 일부).
- 결과가 나온 뒤에는 최소 0.8초 머문다. 결과를 보여주려고 만든 영상이다.

## 텍스트
```js
// 단어 단위 순차 등장 — 애플 타이포의 핵심. 헤드라인은 <span class="w">로 단어를 감싼다
function words(el,lt,start,gap=.14){[...el.querySelectorAll('.w')].forEach((w,i)=>{
  const k=eo(p(lt,start+i*gap,start+i*gap+.55));
  w.style.opacity=k; w.style.transform=`translateY(${(1-k)*60}px)`; w.style.filter=`blur(${(1-k)*14}px)`;});}
// 퇴장: 위로 밀려나며 페이드, 또는 scale(1→.85) + 페이드 (0.3~0.4초)
function wordsOut(el,lt,start){const k=eio(p(lt,start,start+.35));
  el.style.opacity=1-k; el.style.transform=`translateY(${-k*40}px)`;}
// 키워드 교체: 같은 자리에서 단어만 위로 빠지고 새 단어가 아래서 올라옴 ("빠르게 → 정확하게 → 쉽게")
// 텍스트 하이라이트: background linear-gradient + background-size 0%→100% (eo, .5초)
```

## UI 인터랙션 (손가락은 보여주지 않는다)
```js
// 타이핑: 글자 수를 시간으로 계산. 한글은 초당 12~16자, 커서는 Math.floor(t*2)%2
function typeText(el,lt,start,text,cps=14){const n=Math.floor(Math.max(0,lt-start)*cps);
  el.textContent=text.slice(0,n); el.dataset.caret=(n<text.length||Math.floor(lt*2)%2)?'1':'0';}
// 탭 리플: 200px 원(border 4px) 하나를 재사용
function ripple(el,lt,st,cx,cy,maxR=120,dur=.6){const k=p(lt,st,st+dur);
  el.style.transform=`translate(${cx-100}px,${cy-100}px) scale(${eo(k)*maxR/100})`;
  el.style.opacity=(k>0&&k<1)?1-k:0;}
// 버튼 탭: 눌림 → 채움 → 상태 변화
const tp=p(lt,st,st+.45); btn.style.transform=`scale(${1-Math.sin(Math.min(tp/.4,1)*Math.PI)*.08})`;
fill.style.transform=`scaleX(${eo(p(lt,st+.05,st+.4))})`;   // transform-origin:left
// 채움이 절반을 넘으면 글자색 반전, 완료 시 ✓ 아이콘 + 문구 교체 + spring scale
// 처리 중: 점 3개가 sin(t*10 - i*.9)로 위아래, 또는 스켈레톤 줄에 shimmer(backgroundPosition을 t로)
// 리스트 채움: 결과 항목이 .12초 간격으로 translateY(24→0) + opacity
// 스크롤: 긴 화면은 내부 컨테이너 translateY를 eio로 구간 이동 (등속 스크롤 금지)
// 드래그 앤 드롭: 파일 카드가 곡선 경로(lerp + sin 아치)로 이동 → 드롭존 테두리 포인트 컬러 → 착지 시 spring
// 토글·체크: 체크박스가 spring scale, 체크 표시는 stroke-dashoffset
```

## 데이터·증거
```js
// 숫자 카운트업
el.textContent=Math.round(lerp(0,n,eo(p(lt,st,st+1.2)))).toLocaleString();
// 소수·퍼센트: (lerp(0,n,k)).toFixed(1)+'%'
// 막대 차트: height 또는 scaleY(transform-origin:bottom), 막대마다 .08초 stagger
// 선 차트: SVG path에 pathLength=1, strokeDasharray=1, strokeDashoffset=1-eo(k)
// 도넛/링: stroke-dasharray로 호 길이를 k에 비례
// 연결선 그리기 + 패킷: 선은 dashoffset, 패킷 점은 path.getPointAtLength(len*k)로 위치 계산(measure에서 len 저장)
// 비교 막대: 두 막대가 같은 속도로 자라다 k>.5부터 우리 막대만 계속, 끝나면 포인트 컬러
```

## 연속 변환 — 퀄리티를 가장 크게 좌우한다
요소를 사라지게 하고 새 요소를 띄우는 대신, **같은 요소가 모양을 바꾸며 다음 장면으로 이동**하게 만든다. 인과관계("이 입력이 이 결과가 됐다")가 보여서 내용 전달력이 올라간다.

예: 입력 문장 속 키워드 하이라이트 → 칩으로 떨어져 나옴 → 결과 카드의 빈 자리(slot)에 착지 → 같은 칩이 다음 장면 결과에도 붙어 있음.

```js
// slot 기법: 카드 안에 visibility:hidden 인 자리 요소를 두고 measure()에서 좌표 측정,
// 실제 칩은 카드 밖 absolute 레이어에서 translate로 이동한다
x=lerp(start[0],slot[0],eio(k)); y=lerp(start[1],slot[1],eio(k));
// 크기·모양 변화: width/height/borderRadius를 같은 k로 lerp (칩 → 카드, 아이콘 → 풀스크린)
// 공전(모이는 과정 연출): a=ang+(lt-t0)*.45; [cx+cos(a)*470, cy+sin(a)*250]
// 원래 문맥에 없던 요소를 중앙에서 새로 생성해 합류시키면 "추론/생성했다"는 느낌이 난다
```

## 컷 전환 (페이드 대신 매치컷)
- **UI 줌 전환**: 카드나 폰 화면이 scale 확대되며 풀스크린이 되고, 그 안의 UI가 다음 장면이 된다. 기능 그리드→포커스에 쓴다.
- **자리 비켜주기**: 이전 결과물을 `translateX(-440px) scale(.76)`로 옆으로 밀고, 빈 공간으로 다음 요소가 들어온다. 비트와 비트를 이을 때 기본.
- **원형 와이프**: `clip-path: circle(0→1200px at 중심)`, eio 0.8초. 배경색이 바뀔 때.
- **줌인 매치컷**: 오브젝트의 흰 면을 향해 `scale(1→12)` (가속 `x^3`, 0.8초), 화면이 채워지면 다음 흰 배경 장면. `transform-origin`을 가장 넓은 흰 면에.
- **축소 퇴장**: 그룹 전체를 `scale(1→.1)` + 페이드로 줄이며 엔드카드 등장.
- 다음 장면 레이어는 전환 시작 전까지 숨김을 매 프레임 명시한다 (template의 render가 처리).

## 폰/브라우저 목업 (실제 캡처가 있을 때)
- 부모 `perspective:2000px`, 등장 `rotateY(-25deg→0) rotateX(8deg→0)` + 그림자.
- 캡처 속 UI 요소를 복제해 목업 밖으로 튀어나오게(scale 1.1 + 그림자 강화) 하면 애플식 연출이 된다. 핵심 결과 하나에만.
- 캡처를 여러 장 받으면 목업은 고정하고 화면만 원형 와이프나 가로 슬라이드로 교체한다.

## 장식 (아껴 쓰기 — 영상 전체 2회 이하)
오프닝을 채우는 데 쓰지 않는다. 엔드카드나 결과가 완성되는 순간처럼 **감정적 정점**에만 쓴다.
```js
// 팝업: 말풍선·카드
const k=spring(p(lt,st,st+.9));
el.style.transform=`translateY(${(1-k)*40}px) scale(${.6+.4*k})`; el.style.transformOrigin='left bottom';
// 스쿼시&스트레치 (캐릭터 착지)
const q=p(lt,st,st+1.4), sq=Math.exp(-5*q)*Math.sin(q*22);
char.style.transform=`scale(${k*(1+sq*.14)},${k*(1-sq*.14)})`;
// idle float: translateY(sin(t*2.4)*8px) — 화면에 머무는 캐릭터만
// 파티클 버스트: 점·별·링 20여 개 방사형, 거리 d*eo(k), 중력 +eo(k)^2*40, 1초 안에 소멸
// 로고 리빌: clip-path: inset(0 ${(1-k)*100}% 0 0) + scale 1.08→1, 1초 (엔드카드 전용)
```
- 포커스: 강조 대상에 포인트 컬러 3px 링, 나머지는 opacity .45 (이건 장식이 아니라 정보 전달이라 횟수 제한 없음).
