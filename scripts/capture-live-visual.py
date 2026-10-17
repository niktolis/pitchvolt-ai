"""Capture the deployed PitchVolt UI for human comparison with the approved design.

This is evidence collection, not a pixel-diff acceptance test. The live SSE
stream is time dependent; screen captures are not deterministic golden images.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://pitchvolt.app/")
    parser.add_argument("--output", type=Path, default=Path("artifacts/visual"))
    args = parser.parse_args()
    if not args.url.startswith("https://"):
        raise SystemExit("Refusing non-HTTPS target")
    args.output.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for label, width, height in (
                ("desktop", 1600, 900),
                ("mobile", 390, 844),
            ):
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    device_scale_factor=1,
                    reduced_motion="reduce",
                    color_scheme="dark",
                )
                try:
                    response = page.goto(args.url, wait_until="domcontentloaded", timeout=45000)
                    if response is None or not response.ok:
                        raise RuntimeError(f"{label}: HTTP navigation failed")
                    page.get_by_text("PITCHVOLT", exact=False).first.wait_for(timeout=30000)
                    page.locator(".broadcast-grid").wait_for(timeout=30000)
                    page.locator(".pitch svg").wait_for(timeout=30000)
                    page.evaluate("document.fonts.ready")
                    page.wait_for_timeout(2500)
                    page.screenshot(
                        path=str(args.output / f"pitchvolt-{label}.png"),
                        full_page=True,
                        animations="disabled",
                    )
                    print(f"{label}: title={page.title()!r}, screenshot saved")
                finally:
                    page.close()
        finally:
            browser.close()


if __name__ == "__main__":
    main()
