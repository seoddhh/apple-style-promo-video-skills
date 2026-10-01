#!/usr/bin/env python3
"""렌더 결과 검수용 프레임 그리드와 시간 배분·대비·깜빡임 리포트를 만든다.

페이지의 window.TIMELINE 에서 장면 경계를 읽어 각 장면 중간 프레임과
전환 직전·직후(±0.1s) 프레임을 뽑아 grid.png 로 합친다.

함께 검사하는 것 (경고는 ! 로 출력):
  - 텍스트 대비: 32px 미만 일반 굵기 4.5:1, 32px 이상이거나 700 이상 3:1 (html 이 있을 때, 각 장면 중간 시점)
    배경색은 렌더된 화면에서 글자 상자 안의 가장 흔한 색으로 읽는다 (사진·유리 위 글자도 대략 잡힌다).
  - 깜빡임: 화면 평균 밝기가 크게(±25/255) 밝아졌다 어두워지는 번쩍임이 1초에 3회를 넘으면 경고
    (같은 방향으로 이어지는 변화는 한 번으로 센다. 흑백 디졸브 한 번은 번쩍임이 아니다)

사용 예:
  python3 qa_frames.py promo.mp4 promo.html
  python3 qa_frames.py promo.mp4 promo.html --format 9:16 --style clean   # 렌더할 때와 같은 옵션으로
  python3 qa_frames.py promo.mp4 --times 1.5 3.9 4.1 9      # 시간 직접 지정
"""
import argparse, os, re, subprocess, tempfile
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("html", nargs="?")
ap.add_argument("--format", default="16:9")
ap.add_argument("--times", type=float, nargs="*")
ap.add_argument("--style")
ap.add_argument("--out", default="grid.png")
a = ap.parse_args()

SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}

# 화면에 보이는 텍스트 요소의 글자색·크기·위치를 모은다. 배경색은 실제 렌더 화면 픽셀에서 읽는다
TEXT_JS = r"""() => {
  const out = [], W = innerWidth, H = innerHeight;
  for (const el of document.querySelectorAll('body *')) {
    if (![...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) continue;
    const cs = getComputedStyle(el), r = el.getBoundingClientRect();
    if (cs.visibility !== 'visible' || r.width < 4 || r.height < 4 || r.right < 0 || r.bottom < 0 || r.left > W || r.top > H) continue;
    let op = 1; for (let e = el; e && e !== document.documentElement; e = e.parentElement) op *= +getComputedStyle(e).opacity;
    if (op < .9) continue;                                   // 등장·퇴장 중인 글자는 건너뛴다
    const c = cs.color.match(/[\d.]+/g).map(Number);
    out.push({text: el.textContent.trim().slice(0, 24), color: c.slice(0, 3), alpha: c.length > 3 ? c[3] : 1,
              box: [Math.max(0, r.left), Math.max(0, r.top), Math.min(W, r.right), Math.min(H, r.bottom)],
              size: parseFloat(cs.fontSize), weight: +cs.fontWeight});
  }
  return out;
}"""


def lum(c):
    f = lambda x: x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4
    r, g, b = (v / 255 for v in c)
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def contrast_issues(png, items, t):
    """글자 상자 안에서 가장 흔한 색(글자색과 다른 것)을 배경으로 보고 대비를 계산한다."""
    from collections import Counter
    from io import BytesIO
    im, out = Image.open(BytesIO(png)).convert("RGB"), []
    for it in items:
        x0, y0, x1, y1 = map(int, it["box"])
        if x1 - x0 < 4 or y1 - y0 < 4 or it["alpha"] < .1:   # 그라데이션·스윕 글자(color:transparent)는 건너뛴다
            continue
        crop = im.crop((x0, y0, x1, y1))
        crop.thumbnail((160, 160))
        fg = it["color"]
        common = Counter(tuple(v // 8 * 8 + 4 for v in px) for px in getattr(crop, 'get_flattened_data', crop.getdata)()).most_common(6)
        bg = next((c for c, _ in common if sum(abs(c[i] - fg[i]) for i in range(3)) > 60), None)
        if bg is None:
            continue
        fg = [fg[i] * it["alpha"] + bg[i] * (1 - it["alpha"]) for i in range(3)]
        hi, lo = sorted([lum(fg), lum(bg)], reverse=True)
        ratio = (hi + .05) / (lo + .05)
        need = 3.0 if it["size"] >= 32 or it["weight"] >= 700 else 4.5
        if ratio < need:
            out.append({"text": it["text"], "ratio": round(ratio, 2), "need": need, "size": it["size"], "t": round(t, 2)})
    return out


times, timeline, low_contrast = a.times or [], [], []
if a.html and not a.times:
    from playwright.sync_api import sync_playwright
    W, H = SIZES.get(a.format, SIZES["16:9"])
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto("file://" + os.path.abspath(a.html) + "?format=" + a.format + ("&style=" + a.style if a.style else ""))
        pg.evaluate("init()")
        timeline = pg.evaluate("window.TIMELINE || []")
        for s in timeline:
            t = (s["start"] + s["end"]) / 2
            pg.evaluate(f"render({t})")
            low_contrast += contrast_issues(pg.screenshot(type="png"), pg.evaluate(TEXT_JS), t)
        b.close()
    for s in timeline:
        times.append((s["start"] + s["end"]) / 2)
        if s["start"] > 0:
            times += [s["start"] - 0.1, s["start"] + 0.1]
    times = sorted(set(round(t, 2) for t in times if t >= 0))

if timeline:
    total = max(s["end"] for s in timeline)
    by = {}
    for s in timeline:
        by[s.get("role", "?")] = by.get(s.get("role", "?"), 0) + (s["end"] - s["start"])
    print(f"총 {total:.1f}s")
    for r, d in by.items():
        print(f"  {r:8s} {d:5.1f}s  {d / total * 100:4.0f}%")
    if by.get("hook", 0) / total > 0.15:
        print("  ! 훅이 15%를 넘습니다. 템포 컷을 줄이세요")
    if by.get("beat", 0) / total < 0.45:
        print("  ! 기능 장면(beat)이 45% 미만입니다. 제품이 무엇을 해주는지 더 보여주세요")

if a.html and not a.times:
    if low_contrast:
        seen = set()
        for r in low_contrast:
            if r["text"] in seen: continue
            seen.add(r["text"])
            print(f"  ! 대비 부족 {r['t']:5.2f}s  \"{r['text']}\"  {r['ratio']}:1 (필요 {r['need']}:1, {r['size']:.0f}px)")
    else:
        print("  대비: 화면 텍스트 모두 통과")

# 깜빡임: 프레임별 평균 밝기(YAVG)의 급변 횟수를 1초 창으로 센다
fps_s = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate",
                        "-of", "csv=p=0", a.video], capture_output=True, text=True).stdout.strip() or "30/1"
fps = eval(fps_s)
log = subprocess.run(["ffmpeg", "-i", a.video, "-vf", "scale=96:-2,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-",
                      "-f", "null", "-"], capture_output=True, text=True).stdout
ys = [float(v) for v in re.findall(r"YAVG=([\d.]+)", log)]
# 같은 방향으로 이어진 큰 변화는 하나의 전이로 묶고, 1초 창 안의 전이 수 // 2 를 번쩍임 횟수로 본다
trans, prev = [], 0
for i in range(1, len(ys)):
    d = ys[i] - ys[i - 1]
    sgn = (d >= 25) - (d <= -25)
    if sgn and sgn != prev:
        trans.append(i / fps)
    prev = sgn if sgn else (prev if abs(d) >= 8 else 0)
worst, at = 0, 0.0
for s0 in trans:
    n = sum(1 for j in trans if s0 <= j < s0 + 1) // 2
    if n > worst:
        worst, at = n, s0
if worst > 3:
    print(f"  ! 깜빡임: {at:.2f}s 부근 1초 안에 번쩍임 {worst}회. 초당 3회 이하로 줄이세요")
else:
    print(f"  깜빡임: 통과 (1초 최대 번쩍임 {worst}회)")

tmp = tempfile.mkdtemp()
ims = []
for t in times:
    f = os.path.join(tmp, f"{t:.2f}.png")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", a.video,
                    "-frames:v", "1", "-vf", "scale=640:-2", f], check=True)
    if os.path.exists(f):
        im = Image.open(f).convert("RGB")
        ImageDraw.Draw(im).text((8, 6), f"{t:.2f}s", fill=(255, 0, 80))
        ims.append(im)
if not ims:
    raise SystemExit("추출된 프레임이 없습니다")
w, h = ims[0].size
c = 3 if w > h else 5
g = Image.new("RGB", (w * c, h * ((len(ims) + c - 1) // c)), "white")
for i, im in enumerate(ims):
    g.paste(im, ((i % c) * w, (i // c) * h))
g.save(a.out)
print(f"{a.out}: {len(ims)} frames")
