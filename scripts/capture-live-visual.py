"""Capture the deployed PitchVolt UI for human comparison with the approved design.

This is evidence collection, not a pixel-diff acceptance test. The live SSE
stream is time dependent; screen captures are not deterministic golden images.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import time

from playwright.sync_api import Error as PlaywrightError

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://pitchvolt.app/")
    parser.add_argument("--output", type=Path, default=Path("artifacts/visual"))
    parser.add_argument("--expected-sha", default=None)
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
                    for attempt in range(1, 7):
                        try:
                            response = page.goto(args.url, wait_until="domcontentloaded", timeout=45000)
                            if response is None or not response.ok:
                                raise RuntimeError("HTTP navigation failed")
                            page.locator(".broadcast-grid").wait_for(timeout=15000)
                            page.locator(".pitch svg").wait_for(timeout=15000)
                            break
                        except (PlaywrightError, RuntimeError) as error:
                            if attempt == 6:
                                raise RuntimeError(f"{label}: application not ready") from error
                            time.sleep(5)
                    if args.expected_sha:
                        deployed_sha = page.locator('meta[name="pitchvolt-build"]').get_attribute("content")
                        if deployed_sha != args.expected_sha:
                            raise RuntimeError(
                                f"{label}: deployed SHA {deployed_sha!r} is not "
                                f"expected SHA {args.expected_sha!r}"
                            )
                    if "PitchVolt AI" not in page.title():
                        raise RuntimeError(f"{label}: incorrect title {page.title()!r}")
                    page.evaluate("document.fonts.ready")
                    page.wait_for_timeout(2500)
                    insight = page.locator(".insight-panel").bounding_box()
                    pitch = page.locator(".pitch-panel").bounding_box()
                    moment = page.locator(".key-moment-panel").bounding_box()
                    if not all((insight, pitch, moment)):
                        raise RuntimeError(f"{label}: broadcast panel missing")
                    if label == "desktop" and insight and pitch and moment:
                        if not (
                            insight["x"] < pitch["x"] < moment["x"]
                            and abs(insight["y"] - pitch["y"]) < 12
                            and abs(moment["y"] - pitch["y"]) < 12
                        ):
                            raise RuntimeError("Desktop three-column composition deviates")
                    if label == "mobile":
                        viewport = page.evaluate("document.documentElement.clientWidth")
                        scroll = page.evaluate("document.documentElement.scrollWidth")
                        if scroll > viewport + 2:
                            raise RuntimeError(f"Mobile horizontal overflow: {scroll} > {viewport}")
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
