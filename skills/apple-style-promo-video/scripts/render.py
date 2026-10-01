#!/usr/bin/env python3
"""HTML 장면 페이지를 프레임 단위로 캡처해 MP4로 만든다.

페이지는 window.init(), window.render(t), window.DURATION 을 제공해야 한다 (assets/template.html).

사용 예:
  python3 render.py promo.html                                   # 16:9 전체
  python3 render.py promo.html --format 9:16 --out shorts.mp4
  python3 render.py promo.html --from 5 --to 12 --fps 15 --out preview.mp4   # 부분 프리뷰
  python3 render.py promo.html --style clean --out promo_white.mp4          # 스타일 프리셋만 바꿔 다시 렌더
  python3 render.py promo.html --motion reduced --out promo_reduced.mp4      # 저자극 버전
"""
import argparse, os, subprocess, sys, time
from playwright.sync_api import sync_playwright

SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}

ap = argparse.ArgumentParser()
ap.add_argument("html")
ap.add_argument("--format", default="16:9", choices=SIZES)
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--from", dest="t0", type=float, default=0.0)
ap.add_argument("--to", dest="t1", type=float, default=None, help="기본값: 페이지의 DURATION")
ap.add_argument("--out", default="promo.mp4")
ap.add_argument("--crf", type=int, default=16)
ap.add_argument("--motion", default="full", choices=["full", "reduced"], help="reduced: 이동·블러·스프링 대신 페이드 (페이지의 REDUCED 플래그)")
ap.add_argument("--style", choices=["keynote", "clean", "color", "tempo"], help="페이지의 body 스타일 클래스를 덮어쓴다")
a = ap.parse_args()

W, H = SIZES[a.format]
url = "file://" + os.path.abspath(a.html) + "?format=" + a.format + "&motion=" + a.motion + ("&style=" + a.style if a.style else "")

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": W, "height": H})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(url)
    pg.evaluate("init()")
    pg.wait_for_timeout(300)
    if errors:
        sys.exit("페이지 스크립트 오류: " + "; ".join(errors))
    dur = pg.evaluate("window.DURATION || null")
    t1 = a.t1 if a.t1 is not None else dur
    if t1 is None:
        sys.exit("--to 를 지정하거나 페이지에 window.DURATION 을 정의하세요")
    n = int(round((t1 - a.t0) * a.fps))
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(a.fps), "-i", "-",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(a.crf), "-preset", "medium",
         "-movflags", "+faststart", a.out],
        stdin=subprocess.PIPE)
    st = time.time()
    for i in range(n):
        pg.evaluate(f"render({a.t0 + i / a.fps})")
        ff.stdin.write(pg.screenshot(type="png"))
        if i and i % (a.fps * 5) == 0:
            print(f"  {i}/{n} frames ({time.time() - st:.0f}s)", flush=True)
    b.close()
    ff.stdin.close()
    ff.wait()
    if errors:
        print("경고: 렌더 중 스크립트 오류 발생 —", "; ".join(errors[:3]))
print(f"done {a.out}  {a.format} {W}x{H}  {t1 - a.t0:.1f}s @ {a.fps}fps  motion={a.motion} style={a.style or 'page'}")
