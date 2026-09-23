# Clicker demo

A Python script (`clicker.py`) that moves your real mouse cursor over a web page and clicks things, plus a demo page (`demo_page.html`) to try it on.

## Run

```
pip install -r requirements.txt
python clicker.py --list     # open the page, print where each target was found
python clicker.py            # open the page and click through the sequence
python clicker.py --no-open  # use a page that's already open
```

### Your own click sequence

List targets in the order to click them. `name*N` repeats a step. The demo page's targets are `start`, `add`, `checkbox`, `like`, `submit`, the text box `username`, and the dropdown: `fruit` plus its options `apple`, `banana` and `cherry`. Any image you capture adds a target of its own (see below).

```
python clicker.py start add*3 like checkbox submit
python clicker.py --file sequence.txt   # one step per line, '#' for comments
```

`--delay` sets the wait in seconds between clicks (default `0.5`). For example, `python clicker.py --delay 2 start add*3` waits 2 seconds between clicks.

### Typing into text boxes

A `name=text` step clicks the text box, selects anything already in it, and types the text, so the text replaces the old contents.

```
python clicker.py "username=Jane Doe" submit
python clicker.py --type-interval 0.15 "username=Jürgen Müller"   # type more slowly
```

- Put quotes around the whole step when the text contains spaces.
- In a sequence file, write `username="Jane Doe"`. A `#` inside quotes is kept as text; outside quotes, it starts a comment.
- On Windows, characters are sent as Unicode rather than as key presses. That means `@`, umlauts and emoji come out correctly whatever your keyboard layout is.
- `\n` and tab in the text press Enter and Tab.
- On a real website, capture the text box with `--capture` like a button. Point at an empty part of the box.

### Dropdown lists

To pick from a dropdown, list two steps: the toggle, then the option.

```
python clicker.py fruit banana submit
```

The option only appears after the menu opens. For each step, the script keeps looking for up to `--timeout` seconds (default 5), so it waits for the menu to open and then clicks the option. `fruit fruit` opens the menu and closes it again.

### Full check of the demo page

`scenarios/full_check.txt` exercises every element on the demo page: buttons, the checkbox, the text box and the dropdown. Its header lists the run command and the end state to expect.

With no sequence given, the script runs the built-in demo sequence. Every name is checked before the mouse moves.

Keep the browser at 100% zoom with the page fully visible. To abort, fling the mouse into any screen corner.

## Using it on a real website

Real sites have no marker colors, so the script looks for a small **image** of each button instead.

1. **Open the site** at the zoom level you'll use when running the script.
2. **Save an image for each button** you want to click:
   ```
   python clicker.py --capture login
   ```
   Switch to the browser. Within 3 seconds, hover over the button's top-left corner. Then, within the next 3 seconds, hover over its bottom-right corner. The script moves the cursor back so the button's hover style isn't captured, then saves `targets/login.png`. Repeat for each button. A cropped screenshot saved as `targets/<name>.png` works too.
3. **Run your sequence** using those names:
   ```
   python clicker.py --url https://example.com login search*2 next
   python clicker.py --no-open --list      # check what's found, without clicking
   ```

Options that matter on real sites:
- `--timeout 5`: how many seconds to keep looking for a target that isn't on screen yet, for example while the next page loads.
- `--confidence 0.85`: how close the match must be. Lower it if a button isn't found, and raise it if the wrong spot gets clicked.
- `--images DIR`: use a different folder of target images, for example one folder per site.

Tips:
- Capture images at the **same zoom level and screen scaling** you'll run at. Matching doesn't handle resizing.
- Only the **primary monitor** is searched. The target must be visible, because the script doesn't scroll.
- Capture a **distinctive** area, such as the button with its label. A plain one-color patch can match anywhere.
- For **dropdowns**, capture the toggle as usual. Then open the menu by hand and run `--capture` for each option you need; opening the menu first gives you the 3-second countdown to do it. Native `<select>` lists work the same way, because their pop-up list is found on the screenshot like anything else.
- When a step repeats, like `next*3`, the script clicks the same spot again without searching. The button may look different while the cursor is resting on it.

## How it finds things

Before each click, the script takes a screenshot and finds the target in it:
- **Image** (`targets/<name>.png`): OpenCV template matching finds the best-matching spot and clicks its center, as long as the match meets `--confidence`.
- **Color** (demo page only): each demo button has its own solid color (magenta, cyan, yellow, green or orange), and the script clicks the center of that color's pixels.

If a name has both an image and a built-in color, the image is used. The demo page's event log and counters show each click as it lands.
