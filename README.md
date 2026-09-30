# Apple-style Promo Video Skill

AI 영상 모델 없이 **HTML/CSS/JS로 장면을 코딩하고, 헤드리스 Chromium으로 프레임 단위 캡처해 ffmpeg로 MP4**를 만드는 에이전트 스킬입니다. 서비스·앱·SaaS·AI 제품·개발자 도구의 홍보영상, 런칭 필름, 기능 소개 쇼츠, 데모데이/IR 발표 영상을 애플 광고풍 모션그래픽(키네틱 타이포, UI 인터랙션, 데이터 시각화)으로 만듭니다.

- 한글과 UI가 깨지지 않습니다 (실제 폰트로 렌더링)
- 타이밍을 프레임 단위로 조절하고, 고치면 바로 다시 렌더링합니다
- 16:9 / 9:16 / 1:1 / 4:5 비율을 파라미터 하나로 바꿉니다

> 만들 수 없는 것: 실사 인물·제품 촬영 느낌, 음악 생성. 음원을 주면 비트에 맞춰 합칩니다.

## 설치

### Claude Code

```
/plugin marketplace add seoddhh/apple-style-promo-video-skills
/plugin install apple-style-promo-video@seoddhh-skills
```

업데이트는 `/plugin marketplace update seoddhh-skills`로 받습니다.

### 기타 에이전트 (Codex, Cursor 등)

```bash
npx skills add seoddhh/apple-style-promo-video-skills
```

또는 `skills/apple-style-promo-video` 폴더를 각 에이전트의 스킬 폴더에 직접 복사합니다.

- Claude Code: `~/.claude/skills/`
- Codex: `~/.codex/skills/` (버전에 따라 `.agents/skills/`)

### claude.ai 웹 / Claude 데스크탑 앱 (채팅)

웹과 데스크탑 앱의 채팅은 같은 계정 설정을 쓰므로, 한 번 업로드하면 양쪽에서 모두 쓸 수 있습니다.

1. 스킬 폴더를 zip으로 묶습니다. zip 최상위에 `apple-style-promo-video/` 폴더가 있어야 합니다.

   ```bash
   cd skills && zip -r apple-style-promo-video.zip apple-style-promo-video
   ```

2. **설정 → Capabilities**에서 **코드 실행 및 파일 생성(Code execution and file creation)** 을 켭니다. 스킬은 코드 실행이 켜져 있어야 동작합니다.
3. 같은 화면의 **Skills** 항목에서 **Upload skill**을 눌러 zip을 올리고, 토글을 켭니다.
4. 새 채팅에서 "우리 앱 20초 홍보영상 만들어줘"처럼 요청하면 스킬이 자동으로 로드됩니다.

> 채팅 환경에서는 Claude의 코드 실행 샌드박스에서 렌더링합니다. 샌드박스의 네트워크 정책에 따라 Playwright/Chromium, ffmpeg, Pretendard 설치가 막힐 수 있습니다. 이 경우 HTML까지만 받아서 로컬에서 `scripts/render.py`로 렌더링하거나, 아래 Claude Code 방식을 쓰세요.
>
> 업로드한 스킬은 계정에 저장된 복사본이라 이 레포가 업데이트돼도 자동으로 바뀌지 않습니다. 새 버전은 zip을 다시 만들어 업로드합니다.

### Claude 데스크탑 앱 (Code 탭)

데스크탑 앱의 Code 탭은 로컬 Claude Code와 같은 `~/.claude` 설정을 씁니다. 터미널에서 위 Claude Code 설치 명령을 한 번 실행해 두면 Code 탭에서도 바로 쓸 수 있습니다. 렌더링은 내 컴퓨터에서 하므로 [필요 환경](#필요-환경)을 로컬에 설치해 두세요.

### Claude Code 웹 (claude.ai/code)

클라우드 세션은 매번 새 환경에서 시작하므로, 작업할 레포의 `.claude/settings.json`에 마켓플레이스와 플러그인을 적어 두면 세션이 시작될 때 자동으로 설치됩니다.

```json
{
  "extraKnownMarketplaces": {
    "seoddhh-skills": {
      "source": { "source": "github", "repo": "seoddhh/apple-style-promo-video-skills" }
    }
  },
  "enabledPlugins": {
    "apple-style-promo-video@seoddhh-skills": true
  }
}
```

### 스킬은 어디서 받아오나요?

공식 Anthropic 플러그인 디렉터리가 아니라 **이 GitHub 레포에서 직접** 받아옵니다.

| 방식 | 받아오는 곳 | 업데이트 |
|---|---|---|
| `/plugin marketplace add` (Claude Code, 데스크탑 Code 탭, claude.ai/code) | GitHub `seoddhh/apple-style-promo-video-skills`를 클론하고, 레포의 `.claude-plugin/marketplace.json`을 목록으로 읽음 | `/plugin marketplace update seoddhh-skills` |
| `npx skills add` | 같은 GitHub 레포 | 명령 재실행 |
| zip 업로드 (claude.ai 웹, 데스크탑 채팅) | 업로드한 zip 파일 (계정에 저장된 복사본) | zip 재업로드 |

`@seoddhh-skills`는 `marketplace.json`의 `name`으로, 이 레포가 제공하는 마켓플레이스 이름입니다. 레포를 private으로 바꾸면 GitHub 인증이 없는 사용자는 설치할 수 없습니다.

## 필요 환경

렌더링은 로컬(또는 코드 실행 환경)에서 이루어집니다.

```bash
brew install ffmpeg                    # 또는 apt install ffmpeg
pip install playwright && python3 -m playwright install chromium
npm i pretendard                       # 한글 폰트 (영문 전용이면 @fontsource/inter)
```

## 사용 예

```
우리 앱 20초 홍보영상 16:9로 만들어줘. https://example.com
```

에이전트는 다음 순서로 진행합니다.

1. **자료 조사 → 제작 브리프**: URL·레포·캡처를 먼저 읽고 브리프 초안을 보여준 뒤 빈칸만 확인
2. **비트 시트 + 샷 리스트**: 핵심 기능마다 맥락 → 행동 → 결과 → 증거
3. **핵심 비트 프리뷰**: 가장 중요한 기능 장면 5~8초를 먼저 렌더해 톤 확인
4. **전체 렌더 + 프레임 QA**: 장면 중간과 전환 전후 프레임을 격자로 뽑아 검수

### 원칙: 내용이 주인공

- 오프닝은 짧게 (전체의 10% 이하). 로고 리빌은 엔드카드에서 한 번만
- 시간의 60% 안팎을 핵심 기능 비트에 사용
- 장식 모션은 영상 전체에서 2회 이하, 모션은 인과관계를 보여줄 때 사용
- 한 화면 한 메시지

## 스크립트 직접 사용

```bash
python3 scripts/render.py promo.html --format 16:9 --out promo.mp4
python3 scripts/render.py promo.html --from 5 --to 12 --fps 15 --out preview.mp4   # 부분 프리뷰
python3 scripts/qa_frames.py promo.mp4 promo.html                                  # 검수용 grid.png
```

## 구조

```
.claude-plugin/marketplace.json     Claude Code 플러그인 마켓플레이스 정의
skills/apple-style-promo-video/
├── SKILL.md                        에이전트가 읽는 스킬 본문
├── assets/template.html            장면 모듈 + render(t) 순수 함수 템플릿
├── references/
│   ├── design-system.md            레이아웃, 안전영역, 텍스트 길이 한도
│   ├── motion-recipes.md           텍스트·UI·전환 모션 레시피
│   ├── scene-catalog.md            장면 유형 (플로우 데모, Before/After, 수치 증거 등)
│   └── story-templates.md          영상 유형별 골격
└── scripts/
    ├── render.py                   Playwright 프레임 캡처 → ffmpeg MP4
    └── qa_frames.py                검수용 프레임 격자 생성
```

## 라이선스

MIT
