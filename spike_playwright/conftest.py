"""Spike fixtures: run tests in Playwright's own Chromium (default) or in your everyday Chrome.

Tests use the `site_page` fixture instead of `page`.

Everyday Chrome (real profile, less automation fingerprinting):
  1. Close all Chrome windows, then start it with a debugging port:
       "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --remote-debugging-port=9222
  2. pytest spike_playwright --cdp http://localhost:9222
"""

import pytest


def pytest_addoption(parser):
    parser.addoption("--cdp", help="attach to a running Chrome at this URL instead of launching Chromium")


@pytest.fixture
def site_page(request, playwright):
    cdp = request.config.getoption("--cdp")
    if not cdp:
        # pytest-playwright's page: honours --headed, --slowmo, --tracing, --screenshot.
        yield request.getfixturevalue("page")
        return
    browser = playwright.chromium.connect_over_cdp(cdp)
    page = browser.contexts[0].new_page()  # a tab in the real profile
    yield page
    page.close()  # leave the user's browser running
