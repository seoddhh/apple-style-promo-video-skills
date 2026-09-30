#!/usr/bin/env python3
"""렌더 결과 검수용 프레임 그리드와 시간 배분 리포트를 만든다.

페이지의 window.TIMELINE 에서 장면 경계를 읽어 각 장면 중간 프레임과
전환 직전·직후(±0.1s) 프레임을 뽑아 grid.png 로 합친다.

사용 예:
  python3 qa_frames.py promo.mp4 promo.html
  python3 qa_frames.py promo.mp4 promo.html --format 9:16
  python3 qa_frames.py promo.mp4 --times 1.5 3.9 4.1 9      # 시간 직접 지정
"""
import argparse, os, subprocess, tempfile
from PIL import Image, ImageDraw

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("html", nargs="?")
ap.add_argument("--format", default="16:9")
ap.add_argument("--times", type=float, nargs="*")
ap.add_argument("--out", default="grid.png")
a = ap.parse_args()

times, timeline = a.times or [], []
if a.html and not a.times:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        pg.goto("file://" + os.path.abspath(a.html) + "?format=" + a.format)
        timeline = pg.evaluate("window.TIMELINE || []"); b.close()
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
    if by.get("hook", 0) / total > 0.10:
        print("  ! 훅이 10%를 넘습니다. 오프닝을 줄이세요")
    if by.get("beat", 0) / total < 0.55:
        print("  ! 핵심 비트가 55% 미만입니다. 내용 장면을 늘리세요")

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
