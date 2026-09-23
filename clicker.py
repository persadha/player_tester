"""Move the real mouse cursor over a web page and click its targets in sequence.

Targets are found on a fresh screenshot before each click, in one of two ways:
  * image: targets/<name>.png is searched for on screen (OpenCV template
    matching). Works on any website; save the images with --capture NAME.
  * color: the built-in demo_page.html gives each button a unique solid color.
An image for a name takes precedence over its built-in color.

Safety: fling the mouse into any screen corner to abort (pyautogui failsafe).
"""

import argparse
import re
import sys
import time
import webbrowser
from pathlib import Path

import cv2
import numpy as np
import pyautogui

HERE = Path(__file__).parent
PAGE = HERE / "demo_page.html"

# Marker colors, must match the CSS in demo_page.html.
COLOR_TARGETS = {
    "start": (0xFF, 0x00, 0xFF),
    "add": (0x00, 0xFF, 0xFF),
    "checkbox": (0xFF, 0xFF, 0x00),
    "like": (0x00, 0xFF, 0x00),
    "submit": (0xFF, 0x80, 0x00),
    # Dropdown: "fruit" opens the menu; the options are only on screen while it's open.
    "fruit": (0x00, 0x80, 0xFF),
    "apple": (0xFF, 0x00, 0x80),
    "banana": (0x80, 0xFF, 0x00),
    "cherry": (0x80, 0x00, 0xFF),
}

SEQUENCE = ["start", "add", "add", "add", "checkbox", "like", "fruit", "banana", "submit"]

MIN_PIXELS = 200  # color mode: ignore stray pixels that happen to match


def open_page(url, wait):
    webbrowser.open(url or PAGE.resolve().as_uri())
    print(f"Opened {url or PAGE.name}; waiting {wait}s for it to load...")
    time.sleep(wait)


def grab_screen():
    """Screenshot of the primary monitor as an RGB uint8 array."""
    return np.asarray(pyautogui.screenshot().convert("RGB"))


def load_targets(image_dir):
    """Map target name -> ("image", BGR array) or ("color", rgb). Images win."""
    targets = {name: ("color", rgb) for name, rgb in COLOR_TARGETS.items()}
    for png in sorted(Path(image_dir).glob("*.png")):
        img = cv2.imread(str(png), cv2.IMREAD_COLOR)
        if img is None:
            sys.exit(f"Could not read image {png}")
        targets[png.stem.lower()] = ("image", img)
    return targets


def find_color(rgb, screen, tol=20):
    """Return ((x, y) center of pixels matching rgb, detail) or (None, detail)."""
    diff = np.abs(screen.astype(np.int16) - np.array(rgb, dtype=np.int16)).max(axis=2)
    ys, xs = np.nonzero(diff <= tol)
    if len(xs) < MIN_PIXELS:
        return None, f"{len(xs)} matching pixels"
    return (int(xs.mean()), int(ys.mean())), "color"


def find_image(template, screen, confidence):
    """Return ((x, y) center of the best match, detail) or (None, detail) if below confidence."""
    th, tw = template.shape[:2]
    if th > screen.shape[0] or tw > screen.shape[1]:
        return None, "image larger than screen"
    scores = cv2.matchTemplate(cv2.cvtColor(screen, cv2.COLOR_RGB2BGR), template, cv2.TM_CCOEFF_NORMED)
    _, best, _, (x, y) = cv2.minMaxLoc(scores)
    if not best >= confidence:  # also rejects NaN from flat, single-color images
        return None, f"best match {best:.2f} < {confidence}"
    return (x + tw // 2, y + th // 2), f"match {best:.2f}"


def locate(target, screen, confidence):
    kind, data = target
    return find_image(data, screen, confidence) if kind == "image" else find_color(data, screen)


def wait_for(name, target, confidence, timeout):
    """Poll the screen until the target appears or timeout seconds pass."""
    deadline = time.monotonic() + timeout
    while True:
        pos, detail = locate(target, grab_screen(), confidence)
        if pos or time.monotonic() >= deadline:
            return pos, detail
        time.sleep(0.25)


def click_at(name, pos, detail, duration):
    pyautogui.moveTo(*pos, duration=duration, tween=pyautogui.easeInOutQuad)
    pyautogui.click()
    print(f"Clicked {name:<12} at {pos}  ({detail})")


def list_targets(targets, confidence):
    screen = grab_screen()
    for name, target in targets.items():
        pos, detail = locate(target, screen, confidence)
        print(f"{name:<12} {target[0]:<6} {str(pos) if pos else 'NOT FOUND':<12} {detail}")


def countdown_position(prompt, seconds=3):
    for i in range(seconds, 0, -1):
        print(f"  {prompt} ... {i}", end="\r", flush=True)
        time.sleep(1)
    pos = pyautogui.position()
    print(f"  {prompt} ... got {tuple(pos)}   ")
    return pos


def capture(name, image_dir):
    """Save a screenshot of an on-screen element as image_dir/<name>.png."""
    if not re.fullmatch(r"[a-z0-9_-]+", name):
        sys.exit("Capture name may only use lowercase letters, digits, '_' and '-'.")
    home = pyautogui.position()
    print(f"Capturing '{name}'. Switch to the browser and point at the element:")
    x1, y1 = countdown_position("Hover over its TOP-LEFT corner")
    x2, y2 = countdown_position("Hover over its BOTTOM-RIGHT corner")
    left, top, right, bottom = min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)
    if right - left < 8 or bottom - top < 8:
        sys.exit("Region too small; point at opposite corners of the element.")

    # Move the cursor off the element so its hover style isn't captured.
    pyautogui.moveTo(*home)
    time.sleep(0.4)
    region = grab_screen()[top:bottom, left:right]
    path = Path(image_dir) / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), cv2.cvtColor(region, cv2.COLOR_RGB2BGR))
    print(f"Saved {path} ({right - left}x{bottom - top} px)")


def parse_sequence(steps, targets):
    """Expand steps like ["start", "add*3"] into target names, validating each one."""
    names = []
    for step in steps:
        name, _, count = step.strip().lower().partition("*")
        if name not in targets:
            sys.exit(f"Unknown target '{name}'. Choose from: {', '.join(targets)}")
        if count and not count.isdigit():
            sys.exit(f"Bad repeat count in '{step}'; use e.g. add*3")
        names += [name] * int(count or 1)
    return names


def read_sequence_file(path):
    """One step per line (or several separated by spaces); '#' starts a comment."""
    steps = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        steps += line.split("#", 1)[0].split()
    return steps


def main():
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        epilog="Example: python clicker.py --url https://example.com --no-open login search*2",
    )
    parser.add_argument("steps", nargs="*", help="targets to click in order; name*N repeats (default: built-in demo sequence)")
    parser.add_argument("-f", "--file", help="read the sequence from a text file instead")
    parser.add_argument("--url", help="page to open (default: demo_page.html)")
    parser.add_argument("--no-open", action="store_true", help="don't open a page; use the one already on screen")
    parser.add_argument("--images", default=str(HERE / "targets"), help="folder of <name>.png target images (default: targets/)")
    parser.add_argument("--capture", metavar="NAME", help="save an on-screen element as <images>/NAME.png, then exit")
    parser.add_argument("--confidence", type=float, default=0.85, help="image match threshold 0-1 (default 0.85)")
    parser.add_argument("--timeout", type=float, default=5, help="seconds to keep looking for each target (default 5)")
    parser.add_argument("--wait", type=float, default=3, help="seconds to wait for the page to load (default 3)")
    parser.add_argument("--speed", type=float, default=0.6, help="seconds per cursor movement (default 0.6)")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds to wait between clicks (default 0.5)")
    parser.add_argument("--list", action="store_true", help="only print where each target was found; don't click")
    args = parser.parse_args()

    if min(args.delay, args.speed, args.timeout, args.wait) < 0:
        parser.error("--delay, --speed, --timeout and --wait must be 0 or more")
    if not 0 < args.confidence <= 1:
        parser.error("--confidence must be between 0 and 1")

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.3  # pause after every pyautogui call

    if args.capture:
        capture(args.capture.lower(), args.images)
        return

    targets = load_targets(args.images)
    if args.file and args.steps:
        parser.error("give the sequence either as arguments or with --file, not both")
    steps = read_sequence_file(args.file) if args.file else args.steps
    sequence = parse_sequence(steps, targets) if steps else SEQUENCE
    if not sequence:
        sys.exit("Sequence is empty.")
    print("Sequence:", " -> ".join(sequence))

    if not args.no_open:
        open_page(args.url, args.wait)

    if args.list:
        list_targets(targets, args.confidence)
        return

    for i in range(3, 0, -1):
        print(f"Starting in {i}... (move mouse to a screen corner to abort)")
        time.sleep(1)

    prev_name, prev_pos = None, None
    for i, name in enumerate(sequence):
        if i:
            time.sleep(args.delay)
        if name == prev_name:
            # Repeat click: the cursor is resting on the element and its hover
            # style may no longer match the image, so reuse the last position.
            click_at(name, prev_pos, "repeat", args.speed)
            continue
        pos, detail = wait_for(name, targets[name], args.confidence, args.timeout)
        if pos is None:
            sys.exit(f"Target '{name}' not found on screen after {args.timeout}s ({detail}).")
        click_at(name, pos, detail, args.speed)
        prev_name, prev_pos = name, pos
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except pyautogui.FailSafeException:
        sys.exit("Aborted: mouse moved to a screen corner.")
