#!/usr/bin/env python3
"""
SCI-3455 — steps 1–8 in browser (Gmail Email-to-Case + QAFull Case checks/edits).

Prereqs:
  pip install playwright
  python -m playwright install chromium

Usage:
  python3 sci3455_browser.py
  python3 sci3455_browser.py --login-grace 180
  python3 sci3455_browser.py --case-url 'https://sixt3--qafull.../Case/500.../view'
  python3 sci3455_browser.py --skip-gmail --case-url '...'   # steps 3–8 only
  python3 sci3455_browser.py --prestage   # service.prestage@sixt.fr
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.parse
from pathlib import Path

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    from playwright.sync_api import sync_playwright
except ImportError:
    print(
        "Install: pip install playwright && python -m playwright install chromium",
        file=sys.stderr,
    )
    raise

OUT = Path(__file__).resolve().parent
SUBJECT = "Problème d'application"
BODY = """Bonjour,
Problème avec l'application.
Merci, Pooja"""
CASE_TYPE_EXPECTED = "1 Customer Account"
CASE_REASON_EXPECTED = "1.4 Customer Relations"
SUB_REASON_VALUE = "1.4.1 SIXT Voucher"
OWNER_T2 = "T2_Standard"
OWNER_T1_PATTERNS = ("T1_After_Rental", "T1_after_RENTAL")

QAFULL_BASE = "https://sixt3--qafull.sandbox.lightning.force.com"
CASES_RECENT = f"{QAFULL_BASE}/lightning/o/Case/list?filterName=__Recent"


def _gmail_compose_url(to_addr: str) -> str:
    q = urllib.parse.urlencode(
        {
            "view": "cm",
            "fs": "1",
            "to": to_addr,
            "su": SUBJECT,
            "body": BODY,
        }
    )
    return f"https://mail.google.com/mail/u/0/?{q}"


def _shot(page, name: str) -> Path:
    p = OUT / f"{name}.png"
    page.screenshot(path=str(p), full_page=True)
    return p


def _wait_grace_or_enter(login_grace: int | None, msg: str) -> None:
    if login_grace is not None:
        print(f"{msg} (waiting {login_grace}s)…")
        time.sleep(login_grace)
    else:
        input(f"{msg} — press Enter to continue… ")


def _body_text(page) -> str:
    try:
        return page.locator("body").inner_text(timeout=15000)
    except Exception:
        return ""


def step1_2_gmail_send(page, compose_url: str, login_grace: int | None) -> None:
    """Steps 1–2: Gmail login (manual if needed) + send compose."""
    print("[1] Gmail: open session (log in manually if this is a fresh browser profile).")
    page.goto(compose_url, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(2500)
    _shot(page, "sci3455_step1_gmail")

    # If not on compose, user may need to sign in — give time first
    if "accounts.google.com" in (page.url or ""):
        print("[1] Google account sign-in page detected — complete login in the browser.")
        _wait_grace_or_enter(login_grace, "After Gmail is logged in and compose is ready")
        page.goto(compose_url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(2500)

    print("[2] Gmail: attempting to click Send (skip if you already sent).")
    sent = False
    for sel in (
        lambda: page.get_by_role("button", name=re.compile(r"^\s*send\s*$", re.I)),
        lambda: page.locator('[role="button"][aria-label*="Send"]').first,
        lambda: page.locator('div[role="button"]').filter(has_text=re.compile(r"^Send$")),
    ):
        try:
            btn = sel()
            btn.first.click(timeout=8000)
            page.wait_for_timeout(2000)
            sent = True
            print("[2] Send clicked.")
            break
        except Exception:
            continue

    if not sent:
        print("[2] Could not auto-click Send — send the message manually in Gmail.")
        _wait_grace_or_enter(login_grace, "After the email has been sent")

    _shot(page, "sci3455_step2_after_send")


def step3_open_case_from_list(page, case_url: str | None, login_grace: int | None) -> None:
    """Step 3: Navigate to case (direct URL or Cases list)."""
    if case_url:
        print(f"[3] Opening case URL: {case_url}")
        page.goto(case_url, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4000)
        _shot(page, "sci3455_step3_case_record")
        return

    print("[3] Cases list (Recent) — open the row for this subject.")
    page.goto(CASES_RECENT, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(3000)
    _shot(page, "sci3455_step3_cases_list")

    # Try to click a case link whose row / link text matches subject
    try:
        link = page.get_by_role("link", name=re.compile(re.escape(SUBJECT[:12]), re.I))
        link.first.click(timeout=15000)
        page.wait_for_timeout(4000)
        _shot(page, "sci3455_step3_case_record")
        print("[3] Opened case from list.")
    except Exception:
        print("[3] Could not find case link automatically — open the case manually, then continue.")
        _wait_grace_or_enter(login_grace, "When the case detail page is visible")


def _click_edit_case(page) -> bool:
    """Highlights panel / header Edit for the case record."""
    candidates = [
        page.get_by_role("button", name=re.compile(r"edit\s*case", re.I)),
        page.get_by_role("button", name=re.compile(r"^edit$", re.I)).first,
        page.locator("button").filter(has_text=re.compile(r"^Edit$")).first,
    ]
    for c in candidates:
        try:
            c.click(timeout=6000)
            page.wait_for_timeout(2000)
            return True
        except Exception:
            continue
    return False


def _pick_lookup_option(page, combobox_label: str, option_substring: str) -> bool:
    """Lightning combobox by accessible name + option."""
    try:
        cb = page.get_by_role("combobox", name=re.compile(combobox_label, re.I))
        cb.first.click(timeout=8000)
        page.wait_for_timeout(600)
        # Filter long lists
        try:
            cb.first.fill(option_substring[:20])
            page.wait_for_timeout(800)
        except Exception:
            pass
        opt = page.get_by_role(
            "option",
            name=re.compile(re.escape(option_substring), re.I),
        )
        opt.first.click(timeout=12000)
        page.wait_for_timeout(600)
        return True
    except Exception:
        return False


def _save_record(page) -> bool:
    for name_pat in (re.compile(r"^save$", re.I), re.compile(r"^save\s*&", re.I)):
        try:
            page.get_by_role("button", name=name_pat).first.click(timeout=10000)
            page.wait_for_timeout(5000)
            return True
        except Exception:
            continue
    return False


def step4_5_classification(page, login_grace: int | None) -> None:
    """Steps 4–5: Verify Case Type / Case Reason; update via Edit if missing."""
    print("[4] Verifying Case Type and Case Reason on the record…")
    page.wait_for_timeout(2000)
    body = _body_text(page)
    ok_type = CASE_TYPE_EXPECTED.lower() in body.lower()
    ok_reason = CASE_REASON_EXPECTED.lower() in body.lower()
    _shot(page, "sci3455_step4_before_classification")

    if ok_type and ok_reason:
        print(f"[4] OK: found “{CASE_TYPE_EXPECTED}” and “{CASE_REASON_EXPECTED}”.")
        print("[5] No update needed.")
        return

    print(f"[4] Missing expected values — [5] opening Edit to set classification.")
    if not _click_edit_case(page):
        print("[5] Edit Case not found — complete steps 4–5 manually in Salesforce.")
        _wait_grace_or_enter(login_grace, "After Case Type / Case Reason are correct and saved")
        return

    _shot(page, "sci3455_step5_edit_modal")

    # Try common API / label names for picklists
    type_labels = ("Case Type", "Type")
    reason_labels = ("Case Reason", "Reason")
    if not ok_type:
        for lbl in type_labels:
            if _pick_lookup_option(page, lbl, CASE_TYPE_EXPECTED):
                print(f"[5] Set Case Type via “{lbl}”.")
                break
    if not ok_reason:
        for lbl in reason_labels:
            if _pick_lookup_option(page, lbl, CASE_REASON_EXPECTED):
                print(f"[5] Set Case Reason via “{lbl}”.")
                break

    if not _save_record(page):
        print("[5] Save not found — save manually.")
        _wait_grace_or_enter(login_grace, "After Save on the case")
    else:
        print("[5] Save clicked.")

    _shot(page, "sci3455_step5_after_classification_save")


def step6_owner_t2(page) -> None:
    print("[6] Verifying Case Owner / routing shows T2_Standard…")
    page.wait_for_timeout(3000)
    body = _body_text(page)
    _shot(page, "sci3455_step6_owner")
    if OWNER_T2.lower() in body.lower():
        print(f"[6] OK: “{OWNER_T2}” appears on the page.")
    else:
        print(f"[6] WARN: “{OWNER_T2}” not found in visible text — check Owner / Skills manually.")


def step7_8_sub_reason(page, login_grace: int | None) -> None:
    """Steps 7–8: Set Case Sub Reason, save, verify T1 owner label."""
    print(f"[7] Setting Case Sub Reason to “{SUB_REASON_VALUE}”…")
    if not _click_edit_case(page):
        print("[7] Edit Case not found — set Sub Reason manually and save.")
        _wait_grace_or_enter(login_grace, "After Sub Reason is saved")
    else:
        sub_labels = ("Case Sub Reason", "Sub Reason", "Subreason")
        for lbl in sub_labels:
            if _pick_lookup_option(page, lbl, SUB_REASON_VALUE):
                print(f"[7] Set via “{lbl}”.")
                break
        else:
            print("[7] Sub Reason combobox not matched — set manually.")

        if not _save_record(page):
            print("[7] Save not found — save manually.")
            _wait_grace_or_enter(login_grace, "After Save")
        else:
            print("[7] Save clicked.")

    page.wait_for_timeout(4000)
    _shot(page, "sci3455_step8_after_subreason")
    body = _body_text(page)
    print("[8] Verifying Case Owner after sub reason change…")
    t1_ok = any(p.lower() in body.lower() for p in OWNER_T1_PATTERNS)
    if t1_ok:
        print(f"[8] OK: found one of {OWNER_T1_PATTERNS} on the page.")
    else:
        print("[8] WARN: T1 After Rental owner text not found — verify Owner in the UI.")


def step3_poll_until_case_visible(
    page, max_wait_s: int, poll_s: int, login_grace: int | None
) -> bool:
    """Refresh Cases Recent until a row/link for SUBJECT appears."""
    deadline = time.time() + max_wait_s
    attempt = 0
    while time.time() < deadline:
        attempt += 1
        print(f"[3] Poll #{attempt}: Cases Recent (up to {max_wait_s}s total)…")
        page.goto(CASES_RECENT, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(2500)
        if "login" in (page.url or "").lower() or "Login" in _body_text(page)[:800]:
            print("[3] Salesforce login may be required — log in in the browser.")
            _wait_grace_or_enter(login_grace, "After Salesforce login and Cases list loads")
            continue
        try:
            page.get_by_role("link", name=re.compile(re.escape(SUBJECT[:12]), re.I)).first.wait_for(
                state="visible", timeout=8000
            )
            print("[3] Case row visible for subject.")
            return True
        except Exception:
            time.sleep(poll_s)
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="SCI-3455 steps 1–8 (Gmail + QAFull)")
    ap.add_argument(
        "--prestage",
        action="store_true",
        help="To: service.prestage@sixt.fr (script default for QAFull is service.qafull@sixt.fr)",
    )
    ap.add_argument(
        "--login-grace",
        type=int,
        metavar="SEC",
        default=120,
        help="Seconds to wait when manual Gmail/SF login or Send is needed (default: 120)",
    )
    ap.add_argument(
        "--no-login-grace",
        action="store_true",
        help="Use Enter prompts instead of --login-grace waits",
    )
    ap.add_argument("--headless", action="store_true", help="Run Chromium headless (fragile for Gmail)")
    ap.add_argument(
        "--case-url",
        default=None,
        help="Open this Case record (skip list polling if combined with --skip-gmail)",
    )
    ap.add_argument(
        "--skip-gmail",
        action="store_true",
        help="Skip steps 1–2; start at Salesforce (need --case-url or existing case in list)",
    )
    ap.add_argument(
        "--poll-max",
        type=int,
        default=300,
        metavar="SEC",
        help="Max seconds to wait for new case on Cases Recent after send (default: 300)",
    )
    ap.add_argument(
        "--poll-interval",
        type=int,
        default=12,
        metavar="SEC",
        help="Seconds between list refreshes when waiting for case (default: 12)",
    )
    args = ap.parse_args()

    login_grace = None if args.no_login_grace else args.login_grace
    to_addr = "service.prestage@sixt.fr" if args.prestage else "service.qafull@sixt.fr"
    compose = _gmail_compose_url(to_addr)

    print("=== SCI-3455 (steps 1–8) ===")
    print(f"Subject: {SUBJECT}")
    print(f"To: {to_addr}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(viewport={"width": 1600, "height": 960})
        page = context.new_page()

        try:
            if not args.skip_gmail:
                step1_2_gmail_send(page, compose, login_grace)
                found = step3_poll_until_case_visible(
                    page, args.poll_max, args.poll_interval, login_grace
                )
                if not found:
                    print("[3] Timed out waiting for case — open Cases Recent manually or use --case-url.")
                    _wait_grace_or_enter(
                        login_grace,
                        "When the case exists, leave Cases list or case URL ready",
                    )
            else:
                print("[1–2] Skipped (--skip-gmail).")

            step3_open_case_from_list(page, args.case_url, login_grace)
            if "/Case/" not in (page.url or "") and not args.case_url:
                print("WARN: URL does not look like a Case record — steps 4–8 may fail.")

            step4_5_classification(page, login_grace)
            step6_owner_t2(page)
            step7_8_sub_reason(page, login_grace)
            _shot(page, "sci3455_final")

        except PlaywrightTimeout as e:
            print(f"Timeout: {e}", file=sys.stderr)
            _shot(page, "sci3455_error_timeout")
            raise
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            _shot(page, "sci3455_error")
            raise
        finally:
            browser.close()

    print(f"Done. Screenshots: {OUT}/sci3455_*.png")


if __name__ == "__main__":
    main()
