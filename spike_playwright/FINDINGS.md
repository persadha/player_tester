# Playwright spike: findings

Decision gate: do new regression tests go into Playwright, or do we keep developing `clicker.py`?

## Setup

```
pip install pytest-playwright
python -m playwright install chromium

python -m pytest spike_playwright                      # headless, Playwright's Chromium
python -m pytest spike_playwright --headed --slowmo 300  # watch it run
python -m pytest spike_playwright --cdp http://localhost:9222   # your everyday Chrome (see conftest.py)
python -m pytest spike_playwright --tracing retain-on-failure --screenshot only-on-failure
python -m playwright show-trace test-results/<test>/trace.zip   # step through a failure
```

Record a new flow: `python -m playwright codegen <url>`. Then rewrite its selectors as `get_by_role`, `get_by_text` or `get_by_label`, and add `expect(...)` assertions.

## Baseline: demo page (2026-09-25)

`test_demo_full_check.py` is `scenarios/full_check.txt` ported to Playwright.

| | clicker.py | Playwright |
|---|---|---|
| Run time | ~40 s (animated cursor, delays) | 1.2 s headless |
| Pass/fail | none, "compare by eye" | 7 assertions; a deliberately wrong value fails with the actual value shown |
| Needs page changes | marker colors in the CSS | none; text and role selectors only |
| Findings | — | Actionability check caught that the checkbox ignores pointer events and the label must be clicked, which is exactly what a person does |

## Real sites (to fill in)

Site: ______  Flows: ______

| Question | Playwright wins if… | Headed Chromium | Everyday Chrome (CDP) |
|---|---|---|---|
| Bot detection | no captcha, block or behavior change over ~10 runs | | |
| Reliability | ≥ 9/10 green runs per flow, no code changes | | |
| Authoring cost | faster to write and fix than capturing images | | |
| Coverage gaps | steps Playwright can't do (native dialog, canvas, captcha step) | | |

## Decision

- [ ] Playwright passes: new tests go in Playwright. `clicker.py` is kept only for the gap steps listed above.
- [ ] Playwright is blocked: keep developing `clicker.py`. Its first feature is assertions (wait-for-image or OCR).
