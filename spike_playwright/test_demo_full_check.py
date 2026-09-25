"""scenarios/full_check.txt ported to Playwright, with the "compare by eye" end state as assertions.

Selectors use visible text and roles only, the way a third-party site would be tested.
"""

from pathlib import Path

from playwright.sync_api import Page, expect

DEMO = (Path(__file__).parent.parent / "demo_page.html").resolve().as_uri()


def stat(page: Page, label: str):
    """The value above a stat's label, e.g. stat(page, "Items") -> the "3" box."""
    return page.locator(".stat", has=page.get_by_text(label, exact=True)).locator("b")


def test_full_check(site_page: Page):
    page = site_page
    page.goto(DEMO)

    page.get_by_role("button", name="Start").click()
    for _ in range(3):
        page.get_by_role("button", name="Add item").click()
    for _ in range(3):
        page.get_by_text("I agree").click()  # the label; the box itself ignores pointer events
    for _ in range(2):
        page.get_by_role("button", name="Like").click()

    name_box = page.get_by_label("Your name")
    name_box.fill("Jane Doe")
    name_box.fill("Jürgen Müller @ IEA")  # must overwrite, not append

    fruit = page.get_by_role("button", name="Fruit:")
    for option in ("Apple", "Banana", "Cherry"):
        fruit.click()
        page.get_by_role("button", name=option, exact=True).click()
    fruit.click()  # open
    fruit.click()  # close
    fruit.click()
    name_box.click()  # click outside closes the menu
    expect(page.get_by_role("listbox")).to_be_hidden()

    page.get_by_role("button", name="Submit").click()

    expect(stat(page, "Started")).to_have_text("Yes")
    expect(stat(page, "Items")).to_have_text("3")
    expect(stat(page, "Agreed")).to_have_text("Yes")
    expect(stat(page, "Likes")).to_have_text("2")
    expect(stat(page, "Name")).to_have_text("Jürgen Müller @ IEA")
    expect(stat(page, "Fruit")).to_have_text("Cherry")
    log = page.locator("#log li")
    expect(log.first).to_contain_text(
        'Submitted: started=true, items=3, agreed=true, likes=2, fruit=Cherry, name="Jürgen Müller @ IEA"'
    )
    expect(page.locator("#log")).not_to_contain_text("Jane Doe")
