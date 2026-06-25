import asyncio
import hashlib
import re
import socket
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from loguru import logger
from playwright.sync_api import sync_playwright, Browser, Page

from src.config.settings import settings


@dataclass
class VICIdialSession:
    playwright_obj: Any
    browser: Browser
    page: Page
    agent_serial: str
    executor: ThreadPoolExecutor


class VICIdialController:

    def __init__(self):
        self._sessions: dict[str, VICIdialSession] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    async def _run_on_thread(executor: ThreadPoolExecutor, fn, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(executor, lambda: fn(*args, **kwargs))

    @staticmethod
    def _find_frame_with(page, selector, timeout=15000):
        for f in page.frames:
            try:
                f.wait_for_selector(selector, timeout=timeout)
                return f
            except Exception:
                continue
        return None

    @staticmethod
    def _handle_session_conflict(page) -> bool:
        import time as _time

        conflict_detected = False
        for f in page.frames:
            try:
                if f.get_by_text("Another live agent session", exact=False).count() > 0:
                    conflict_detected = True
                    break
            except Exception:
                continue

        if not conflict_detected:
            return False

        logger.info("Session conflict detected — clearing stale session")

        for f in page.frames:
            try:
                logout_btn = f.locator(
                    'button:has-text("Logout"), '
                    'a:has-text("Logout"), '
                    'input[value="Logout"]'
                )
                if logout_btn.count() > 0 and logout_btn.first.is_visible():
                    logger.info("Found Logout button — force-closing zombie session")
                    logout_btn.first.click(timeout=5000)
                    _time.sleep(3)
                    page.wait_for_load_state("networkidle", timeout=30000)
                    break
            except Exception:
                continue

        try:
            page.wait_for_selector('#LoadingBox', state='hidden', timeout=15000)
        except Exception:
            pass

        ok_clicked = False
        for f in page.frames:
            try:
                ok_btn = f.locator(
                    '//a[contains(text(), "OK")] | '
                    '//span[contains(text(), "OK")] | '
                    '//button[contains(text(), "OK")] | '
                    '//input[@value="OK"]'
                )
                if ok_btn.count() > 0 and ok_btn.first.is_visible():
                    logger.info("Clicking OK to clear stale session")
                    ok_btn.first.click(force=True, timeout=5000)
                    ok_clicked = True
                    _time.sleep(2)
                    break
            except Exception:
                continue

        if not ok_clicked:
            logger.warning("Session conflict overlay found but OK link was not clickable")
            return False

        import time as _time2
        deadline = _time2.time() + 45
        while _time2.time() < deadline:
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            current_url = page.url
            if "login" not in current_url.lower() and "conflict" not in current_url.lower():
                for f in page.frames:
                    try:
                        paused = f.locator(
                            '//a[contains(text(), "PAUSED")] | '
                            '//span[contains(text(), "PAUSED")] | '
                            '//button[contains(text(), "PAUSED")] | '
                            '//*[contains(text(), "YOU ARE PAUSED")]'
                        )
                        if paused.count() > 0 and paused.first.is_visible():
                            logger.info(
                                "PAUSED button visible — session conflict resolved"
                            )
                            return True
                    except Exception:
                        continue
            _time2.sleep(2)

        logger.warning(
            "Session conflict overlay clicked but PAUSED button "
            "did not appear within timeout — continuing anyway"
        )
        return True

    @staticmethod
    def _dismiss_ok_popup(page) -> bool:
        import time as _time

        SELECTORS = (
            '//a[contains(text(), "OK")] | '
            '//span[contains(text(), "OK")] | '
            '//button[contains(text(), "OK")] | '
            '//input[@value="OK"] | '
            '//div[contains(text(), "OK")] | '
            '//*[@id="OK"] | '
            '//*[contains(@class, "ok") and contains(text(), "OK")]'
        )

        def _popup_visible() -> bool:
            for f in page.frames:
                try:
                    btn = f.locator(SELECTORS)
                    if btn.count() > 0 and btn.first.is_visible():
                        return True
                except Exception:
                    continue
            return False

        def _click_standard(f) -> bool:
            btn = f.locator(SELECTORS)
            if btn.count() == 0 or not btn.first.is_visible():
                return False
            btn.first.click(force=True, timeout=5000)
            return True

        def _click_js(f) -> bool:
            btn = f.locator(SELECTORS)
            if btn.count() == 0 or not btn.first.is_visible():
                return False
            btn.first.evaluate("el => el.click()")
            return True

        # ── Phase 1: Standard Playwright click (3 attempts) ──────────
        for attempt in range(3):
            for f in page.frames:
                try:
                    if not _popup_visible():
                        return True
                    logger.info(f"OK popup — standard click attempt {attempt + 1}/3")
                    _click_standard(f)
                    _time.sleep(2)
                    if not _popup_visible():
                        logger.info("OK popup dismissed via standard click")
                        return True
                except Exception:
                    continue
            _time.sleep(1)

        # ── Phase 2: JavaScript click fallback (2 attempts) ──────────
        for attempt in range(2):
            for f in page.frames:
                try:
                    if not _popup_visible():
                        return True
                    logger.info(f"OK popup — JS click attempt {attempt + 1}/2")
                    _click_js(f)
                    _time.sleep(2)
                    if not _popup_visible():
                        logger.info("OK popup dismissed via JS click")
                        return True
                except Exception:
                    continue
            _time.sleep(1)

        # ── Phase 3: Page refresh to clear stale session lock ───────
        logger.warning("OK popup not dismissed by click — performing page refresh")
        try:
            page.reload(timeout=90000)
            page.wait_for_load_state("domcontentloaded")
            _time.sleep(3)
            if not _popup_visible():
                logger.info("OK popup cleared after page refresh")
                return True
            logger.warning("OK popup still visible after page refresh")
        except Exception as e:
            logger.error(f"Page refresh failed: {e}")

        return False

    @staticmethod
    def _click_ready_button(page) -> bool:
        import time as _time

        for attempt in range(5):
            for f in page.frames:
                try:
                    ready_btn = f.locator(
                        '//a[contains(text(), "READY")] | '
                        '//span[contains(text(), "READY")] | '
                        '//button[contains(text(), "READY")] | '
                        '//input[@value="READY"] | '
                        '//a[contains(text(), "YOU ARE PAUSED")] | '
                        '//span[contains(text(), "YOU ARE PAUSED")] | '
                        '//button[contains(text(), "YOU ARE PAUSED")] | '
                        '//a[contains(text(), "PAUSED")] | '
                        '//span[contains(text(), "PAUSED")] | '
                        '//button[contains(text(), "PAUSED")] | '
                        '//a[contains(text(), "Resume")] | '
                        '//span[contains(text(), "Resume")] | '
                        '//button[contains(text(), "Resume")]'
                    )
                    if ready_btn.count() > 0 and ready_btn.first.is_visible():
                        label = ready_btn.first.inner_text().strip()
                        logger.info(f"Clicking '{label}' button to set agent READY")
                        ready_btn.first.click(force=True, timeout=5000)
                        _time.sleep(2)
                        return True
                except Exception:
                    continue
            _time.sleep(1)

        logger.warning("No READY or PAUSED/Resume button found after login")
        return False

    @staticmethod
    def _check_sip_port(server_ip: str, port: int = 5061) -> str:
        try:
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.settimeout(3)
            result = tcp_sock.connect_ex((server_ip, port))
            tcp_sock.close()
            if result == 0:
                return "Open"
            return "Closed"
        except Exception:
            return "Closed"

    def _sip_register(self) -> bool:
        server_ip = settings.sip_server_ip
        extension = settings.sip_extension
        password = settings.sip_registration_password

        logger.debug(
            f"SIP config loaded — server={server_ip!r}, "
            f"ext={extension!r}, pass={'*' * len(password) if password else '<empty>'}"
        )

        if not server_ip or not extension or not password:
            logger.error(
                "SIP config missing — set SIP_SERVER_IP, SIP_EXTENSION, "
                "and SIP_REGISTRATION_PASSWORD in .env"
            )
            return False

        tag = uuid.uuid4().hex[:8]
        local_port = 5061
        max_attempts = 3
        last_error: str | None = None

        logger.info("Running network diagnosis for SIP...")
        port_status = VICIdialController._check_sip_port(server_ip, 5061)
        logger.info(f"Port 5061 status: {port_status}")
        if port_status == "Closed":
            logger.error(
                "CRITICAL: Port 5061 is blocked by your network/ISP. "
                "Please check firewall rules or use SIP_BYPASS=true"
            )
            return False

        def _build_register(
            cseq: int, branch_val: str, call_id: str, auth_header: str = ""
        ):
            hdrs = (
                f"REGISTER sip:{server_ip} SIP/2.0\r\n"
                f"Via: SIP/2.0/UDP 0.0.0.0:{local_port};branch={branch_val};rport\r\n"
                f"Max-Forwards: 70\r\n"
                f"From: <sip:{extension}@{server_ip}>;tag={tag}\r\n"
                f"To: <sip:{extension}@{server_ip}>\r\n"
                f"Call-ID: {call_id}\r\n"
                f"CSeq: {cseq} REGISTER\r\n"
                f"Contact: <sip:{extension}@0.0.0.0:{local_port}>\r\n"
            )
            if auth_header:
                hdrs += auth_header
            hdrs += f"Expires: 3600\r\nContent-Length: 0\r\n\r\n"
            return hdrs

        def _parse_digest_param(response_text: str, param: str) -> str:
            import re as _re
            m = _re.search(r'(?i)' + param + r'\s*=\s*"([^"]+)"', response_text)
            return m.group(1) if m else ""

        for attempt in range(1, max_attempts + 1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(10)

            try:
                logger.info(
                    f"SIP registration attempt {attempt}/{max_attempts} — "
                    f"{extension}@{server_ip}:5061"
                )

                call_id = f"{uuid.uuid4().hex}@0.0.0.0"
                branch = f"z9hG4bK{uuid.uuid4().hex[:8]}"
                msg1 = _build_register(1, branch, call_id)
                sock.sendto(msg1.encode(), (server_ip, 5061))
                data, _ = sock.recvfrom(4096)
                resp = data.decode(errors="replace")

                if "200 OK" in resp:
                    logger.info(
                        f"SIP REGISTRATION SUCCESSFUL — "
                        f"{extension}@{server_ip} (no auth needed)"
                    )
                    return True

                if "401 Unauthorized" not in resp:
                    logger.warning(
                        f"Unexpected SIP response (expected 401): "
                        f"{resp[:200].strip()}"
                    )
                    last_error = f"unexpected response: {resp[:100].strip()}"
                    break

                realm = _parse_digest_param(resp, "realm")
                nonce = _parse_digest_param(resp, "nonce")
                if not realm or not nonce:
                    logger.error(
                        f"SIP 401 missing realm/nonce. Response: {resp[:300]}"
                    )
                    last_error = "401 missing realm/nonce"
                    break

                logger.debug(f"SIP challenge received — realm={realm}")

                ha1 = hashlib.md5(
                    f"{extension}:{realm}:{password}".encode()
                ).hexdigest()
                ha2 = hashlib.md5(
                    f"REGISTER:sip:{server_ip}".encode()
                ).hexdigest()
                digest = hashlib.md5(
                    f"{ha1}:{nonce}:{ha2}".encode()
                ).hexdigest()

                auth_hdr = (
                    f"Authorization: Digest username=\"{extension}\","
                    f"realm=\"{realm}\",nonce=\"{nonce}\","
                    f"uri=\"sip:{server_ip}\","
                    f"response=\"{digest}\"\r\n"
                )

                branch2 = f"z9hG4bK{uuid.uuid4().hex[:8]}"
                msg2 = _build_register(2, branch2, call_id, auth_hdr)
                sock.sendto(msg2.encode(), (server_ip, 5061))
                data, _ = sock.recvfrom(4096)
                resp2 = data.decode(errors="replace")

                if "200 OK" in resp2:
                    logger.info(
                        f"SIP REGISTRATION SUCCESSFUL — "
                        f"{extension}@{server_ip}"
                    )
                    return True

                logger.error(
                    f"SIP registration failed after auth. "
                    f"Response: {resp2[:300].strip()}"
                )
                last_error = f"auth failed: {resp2[:100].strip()}"
                break

            except socket.timeout:
                last_error = (
                    f"timeout connecting to {server_ip}:5061 "
                    f"(attempt {attempt}/{max_attempts})"
                )
                logger.warning(last_error)
            except OSError as e:
                last_error = f"socket error: {e}"
                logger.warning(
                    f"SIP attempt {attempt}/{max_attempts} failed — "
                    f"{last_error}"
                )
            finally:
                sock.close()

            if attempt < max_attempts:
                import time as _time
                _time.sleep(5)

        logger.error(
            f"SIP REGISTRATION FAILED after {max_attempts} attempts. "
            f"Last error: {last_error}. "
            f"Check: (1) server IP is correct ({server_ip}), "
            f"(2) port 5061 is open on firewall, "
            f"(3) server is reachable from this network."
        )
        return False

    async def login(self, bot_id: str) -> bool:
        if settings.sip_bypass:
            logger.info("SIP_BYPASS active: proceeding to login without audio")
        elif not self._sip_register():
            logger.error(
                f"SIP REGISTRATION FAILED for {bot_id} — "
                f"will not proceed to login page"
            )
            return False

        async with self._lock:
            if bot_id in self._sessions:
                logger.warning(f"Bot {bot_id} already logged in")
                return True

            executor = ThreadPoolExecutor(
                max_workers=1, thread_name_prefix=f"pw-{bot_id}"
            )

            def _do_login():
                import time as _time

                def _retry_nav(fn, max_retries=3, delay=10):
                    for attempt in range(1, max_retries + 1):
                        try:
                            return fn()
                        except Exception as e:
                            if attempt < max_retries:
                                logger.warning(
                                    f"Nav failed (attempt {attempt}/{max_retries}): {e}"
                                )
                                _time.sleep(delay)
                            else:
                                raise

                p = sync_playwright().start()
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        "--use-fake-ui-for-media-stream",
                        "--use-fake-device-for-media-stream",
                        "--disable-notifications",
                    ],
                )
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"
                    )
                )
                context.grant_permissions(
                    ["microphone"], origin="https://calibertechfebots.flexodialer.com"
                )
                page = context.new_page()
                _retry_nav(
                    lambda: page.goto(
                        settings.vicidial_url, timeout=90000
                    )
                )
                page.wait_for_load_state("domcontentloaded")

                f_phone = VICIdialController._find_frame_with(
                    page, 'input[name="phone_login"]', timeout=40000
                )
                if f_phone is None:
                    raise RuntimeError("Phone login fields not found")
                f_phone.locator('input[name="phone_login"]').fill(
                    settings.phone_ext
                )
                f_phone.locator('input[name="phone_pass"]').fill(
                    settings.phone_pass
                )
                f_phone.locator(
                    'input[type="submit"], button[type="submit"], '
                    'input[value="Submit"], input[value="Login"]'
                ).click(timeout=5000, no_wait_after=True)
                page.wait_for_load_state("domcontentloaded")
                logger.info("Phone login submitted successfully")

                still_phone = VICIdialController._find_frame_with(
                    page, 'input[name="phone_login"]', timeout=5000
                )
                if still_phone is not None:
                    logger.error(
                        f"Phone login failed — still on phone login page. "
                        f"URL: {page.url} | Title: {page.title()}"
                    )
                    page.screenshot(path="debug_phone_fail.png")
                    raise RuntimeError(
                        "Phone login failed — check PHONE_EXT / PHONE_PASS in .env"
                    )

                page.wait_for_timeout(2000)
                deadline = _time.time() + 40
                f_camp = None
                while _time.time() < deadline:
                    n_frames = len(page.frames)
                    logger.info(f"Available frames: {n_frames}")
                    if n_frames == 1:
                        if page.locator(
                            'input[name="VD_login"], select[name="VD_campaign"]'
                        ).count() > 0:
                            f_camp = page
                            logger.info("Found form directly on main page")
                            break
                    else:
                        for i, f in enumerate(page.frames):
                            try:
                                url = f.url
                            except Exception:
                                url = "<error>"
                            logger.info(f"  Frame[{i}]: {url}")
                        f_camp = page.frames[1]
                        if f_camp.locator(
                            'input[name="VD_login"], select[name="VD_campaign"]'
                        ).count() > 0:
                            logger.info(
                                f"Found form in frame[1]: {f_camp.url}"
                            )
                            break
                        else:
                            f_camp = None
                    _time.sleep(1)
                if f_camp is None:
                    logger.error(
                        f"Campaign login form not found. "
                        f"Current URL: {page.url}"
                    )
                    logger.error(f"Page HTML:\n{page.content()}")
                    page.screenshot(path="debug_error.png")
                    raise RuntimeError("Campaign login form not found")

                f_camp.locator('input[name="VD_login"]').click()
                f_camp.locator('input[name="VD_login"]').fill(
                    settings.vicidial_user
                )
                if (
                    f_camp.locator('input[name="VD_login"]').input_value()
                    != settings.vicidial_user
                ):
                    f_camp.locator('input[name="VD_login"]').type(
                        settings.vicidial_user, delay=50
                    )
                f_camp.locator('input[name="VD_pass"]').click()
                f_camp.locator('input[name="VD_pass"]').fill(
                    settings.vicidial_pass
                )
                if (
                    f_camp.locator('input[name="VD_pass"]').input_value()
                    != settings.vicidial_pass
                ):
                    f_camp.locator('input[name="VD_pass"]').type(
                        settings.vicidial_pass, delay=50
                    )
                logger.info("Campaign user/pass entered")

                f_camp.locator(
                    'select[name="VD_campaign"]'
                ).wait_for(timeout=10000)
                f_camp.locator('select[name="VD_campaign"]').focus()
                _time.sleep(1)
                f_camp.locator(
                    'select[name="VD_campaign"]'
                ).select_option(settings.vicidial_campaign)
                logger.info(
                    f"Campaign '{settings.vicidial_campaign}' selected"
                )

                f_camp.locator(
                    'input[id="login_sub"], input[name="login_sub"]'
                ).click(timeout=5000, no_wait_after=True)
                page.wait_for_load_state("domcontentloaded")
                logger.info("Campaign login submitted")

                def _reenter_campaign_login():
                    """Re-fill campaign login fields after a page reload."""
                    f_phone = VICIdialController._find_frame_with(
                        page, 'input[name="phone_login"]', timeout=10000
                    )
                    if f_phone is not None:
                        f_phone.locator('input[name="phone_login"]').fill(
                            settings.phone_ext
                        )
                        f_phone.locator('input[name="phone_pass"]').fill(
                            settings.phone_pass
                        )
                        f_phone.locator(
                            'input[type="submit"], button[type="submit"], '
                            'input[value="Submit"], input[value="Login"]'
                        ).click(timeout=5000, no_wait_after=True)
                        page.wait_for_load_state("domcontentloaded")
                        logger.info("Phone login re-entered after refresh")

                    nf = VICIdialController._find_frame_with(
                        page,
                        'input[name="VD_login"], select[name="VD_campaign"]',
                        timeout=15000,
                    )
                    if nf is not None:
                        nf.locator('input[name="VD_login"]').fill(
                            settings.vicidial_user
                        )
                        nf.locator('input[name="VD_pass"]').fill(
                            settings.vicidial_pass
                        )
                        nf.locator(
                            'select[name="VD_campaign"]'
                        ).select_option(settings.vicidial_campaign)
                        nf.locator(
                            'input[id="login_sub"], input[name="login_sub"]'
                        ).click(timeout=5000, no_wait_after=True)
                        page.wait_for_load_state("domcontentloaded")
                        logger.info("Campaign login re-entered after refresh")
                        return nf
                    return None

                _time.sleep(2)
                conflict_handled = self._handle_session_conflict(page)
                if not conflict_handled:
                    _retry_nav(lambda: page.reload(timeout=90000))
                page.wait_for_load_state("domcontentloaded")
                loading = page.locator("#LoginLoadingBox")
                if loading.count() > 0 and loading.is_visible():
                    logger.warning("Loading overlay still visible — hiding form")
                    page.evaluate(
                        "document.getElementById('vicidial_form')"
                        " && (document.getElementById('vicidial_form')"
                        ".style.display = 'none')"
                    )

                for _retry in range(2):
                    dismissed = VICIdialController._dismiss_ok_popup(page)
                    VICIdialController._click_ready_button(page)

                    if dismissed:
                        break

                    logger.warning(
                        f"OK popup not dismissed (retry {_retry + 1}) "
                        f"— reloading and re-entering credentials"
                    )
                    _retry_nav(lambda: page.reload(timeout=90000))
                    page.wait_for_load_state("domcontentloaded")
                    _reenter_campaign_login()
                    _time.sleep(2)

                return p, browser, page

            try:
                p, browser, page = await self._run_on_thread(executor, _do_login)
            except Exception as exc:
                executor.shutdown(wait=False)
                logger.error(f"VICIdial login failed for {bot_id}: {exc}")
                return False

            agent_serial = f"AGENT_{bot_id}_{id(self)}"
            self._sessions[bot_id] = VICIdialSession(
                playwright_obj=p,
                browser=browser,
                page=page,
                agent_serial=agent_serial,
                executor=executor,
            )
            logger.info(f"Bot {bot_id} logged into VICIdial")
            return True

    async def _logout_locked(self, bot_id: str):
        session = self._sessions.pop(bot_id, None)
        if session is None:
            return

        def _do_logout():
            try:
                session.page.click('text="Logout"', timeout=5000)
            except Exception:
                pass
            session.browser.close()
            session.playwright_obj.stop()

        try:
            await self._run_on_thread(session.executor, _do_logout)
        except Exception as e:
            logger.warning(f"Logout cleanup error for {bot_id}: {e}")
        finally:
            session.executor.shutdown(wait=False)
            logger.info(f"Bot {bot_id} logged out of VICIdial")

    async def logout(self, bot_id: str):
        async with self._lock:
            await self._logout_locked(bot_id)

    async def set_pause(self, bot_id: str, paused: bool):
        session = self._sessions.get(bot_id)
        if not session:
            raise RuntimeError(f"Bot {bot_id} not logged in")

        btn_text = "Pause" if paused else "Resume"

        def _do_pause():
            session.page.click(f'text="{btn_text}"', timeout=5000)

        await self._run_on_thread(session.executor, _do_pause)
        logger.info(f"Bot {bot_id} {'paused' if paused else 'resumed'}")

    async def get_status(self, bot_id: str) -> str | None:
        session = self._sessions.get(bot_id)
        if not session:
            return None

        def _do_status():
            try:
                el = session.page.query_selector(".agent_status")
                return el.inner_text() if el else "unknown"
            except Exception:
                return "unknown"

        return await self._run_on_thread(session.executor, _do_status)

    async def check_hopper_status(self, bot_id: str) -> str:
        session = self._sessions.get(bot_id)
        if not session:
            return "unknown"

        def _check():
            page = session.page
            body = page.inner_text("body") if page.query_selector("body") else ""
            body_upper = body.upper()

            for phrase in ["HOPPER EMPTY", "HOPPER IS EMPTY",
                           "NO LEADS", "NO MORE LEADS",
                           "NO CALLS TO MAKE", "LEADS: 0",
                           "0 LEADS", "0 CALLS"]:
                if phrase in body_upper:
                    logger.warning(f"Bot {bot_id} — HOPPER EMPTY: Waiting for leads ('{phrase}')")
                    return "empty"

            lead_pats = [
                r'(?:LEADS|CALLS)\s*:?\s*([1-9]\d*)',
                r'AVAILABLE\s+LEADS\s*:?\s*([1-9]\d*)',
                r'HOPPER\s*:?\s*([1-9]\d*)',
                r'QUEUE\s*:?\s*([1-9]\d*)',
            ]
            for pat in lead_pats:
                m = re.search(pat, body_upper)
                if m:
                    count = int(m.group(1))
                    logger.info(f"Bot {bot_id} — hopper has {count} leads")
                    return "ok"

            return "unknown"

        return await self._run_on_thread(session.executor, _check)

    async def detect_dial_method(self, bot_id: str) -> str:
        session = self._sessions.get(bot_id)
        if not session:
            return "unknown"

        def _detect():
            page = session.page
            body = page.inner_text("body") if page.query_selector("body") else ""
            body_upper = body.upper()

            dial_btn = page.locator('text="Dial Next Number"')
            if dial_btn.count() > 0 and dial_btn.is_visible():
                return "MANUAL"

            for method in ["RATIO", "ADAPTIVE", "PREDICTIVE", "PROGRESSIVE"]:
                if method in body_upper:
                    return method

            return "unknown"

        return await self._run_on_thread(session.executor, _detect)

    async def diagnose_campaign(self, bot_id: str) -> dict:
        dial_method = await self.detect_dial_method(bot_id)
        hopper_status = await self.check_hopper_status(bot_id)

        diag = {
            "dial_method": dial_method,
            "hopper_status": hopper_status,
            "issues": [],
        }

        if dial_method != "RATIO":
            msg = (
                f"Campaign dial method is '{dial_method}', expected 'RATIO'. "
                f"Change in VICIdial admin: Admin -> Campaigns -> {settings.vicidial_campaign} "
                f"-> Dial Method = RATIO"
            )
            logger.warning(f"Bot {bot_id} — {msg}")
            diag["issues"].append(msg)

        if hopper_status == "empty":
            msg = (
                f"Hopper is EMPTY for campaign '{settings.vicidial_campaign}'. "
                f"Load leads via VICIdial admin: Admin -> Hopper -> Add Leads, "
                f"or status will remain READY with no calls pushed"
            )
            logger.warning(f"Bot {bot_id} — {msg}")
            diag["issues"].append(msg)
        elif hopper_status == "unknown":
            logger.info(f"Bot {bot_id} — hopper status unclear from UI (no explicit lead count found)")

        if not diag["issues"]:
            logger.info(
                f"Bot {bot_id} — Campaign OK: dial_method=RATIO, hopper has leads. "
                f"Auto-dialer should push calls automatically."
            )

        return diag

    async def resume_agent(self, bot_id: str) -> bool:
        session = self._sessions.get(bot_id)
        if not session:
            raise RuntimeError(f"Bot {bot_id} not logged in")

        def _do_resume():
            import time as _time

            def _get_status() -> str:
                for f in session.page.frames:
                    try:
                        el = f.query_selector(".agent_status")
                        if el:
                            text = el.inner_text().upper()
                            if text.strip():
                                return text
                    except Exception:
                        continue
                return ""

            current = _get_status()
            ready_keywords = ("READY", "WAITING FOR RING")

            if any(kw in current for kw in ready_keywords):
                logger.info(
                    f"Bot {bot_id} already in active state: {current}"
                )
                return True

            paused_found = False
            attempts = 0
            max_attempts = 6

            while not paused_found and attempts < max_attempts:
                attempts += 1

                locators = [
                    ("button", "YOU ARE PAUSED", False),
                    ("link", "YOU ARE PAUSED", False),
                    ("text", "YOU ARE PAUSED", False),
                    ("button", "Resume", False),
                    ("link", "Resume", False),
                    ("text", "Resume", False),
                ]

                for role, name, exact in locators:
                    for f in session.page.frames:
                        try:
                            if role == "text":
                                btn = f.locator(f"text={name}")
                            else:
                                btn = f.get_by_role(role, name=name, exact=exact)
                            if btn.count() > 0:
                                btn.first.wait_for(state="visible", timeout=3000)
                                btn.first.click(timeout=3000)
                                _time.sleep(2)
                                logger.info(
                                    f"Bot {bot_id} — Successfully clicked "
                                    f"'{name}' button (attempt {attempts})"
                                )
                                paused_found = True
                                break
                        except Exception:
                            continue
                    if paused_found:
                        break

                if not paused_found:
                    logger.info(
                        f"Bot {bot_id} — resume button not yet visible, "
                        f"retrying ({attempts}/{max_attempts})..."
                    )
                    _time.sleep(2)

            if paused_found:
                deadline = _time.time() + 15
                while _time.time() < deadline:
                    status = _get_status()
                    if any(kw in status for kw in ready_keywords):
                        logger.info(
                            f"Bot {bot_id} status confirmed as READY: "
                            f"{status}"
                        )
                        return True
                    _time.sleep(0.5)
                logger.warning(
                    f"Bot {bot_id} — clicked pause/resume but status "
                    f"did not become READY. Last status: {_get_status()}"
                )
                return False

            logger.error(
                f"Bot {bot_id} — FAILED: Could not find PAUSED button "
                f"in any frame after {max_attempts} retries. "
                f"Status: {_get_status()}"
            )
            return False

        result = await self._run_on_thread(session.executor, _do_resume)

        if result:
            await self.diagnose_campaign(bot_id)
            logger.info(
                f"Bot {bot_id} — in READY state. "
                f"Server-side dialer will push calls automatically "
                f"when campaign is on RATIO mode with leads in hopper."
            )

        return result

    # ── Live call actions ──────────────────────────────────────────

    @staticmethod
    def _click_dashboard_button(page, *texts: str) -> bool:
        for f in page.frames:
            for text in texts:
                try:
                    btn = f.locator(
                        f'button:has-text("{text}"), '
                        f'a:has-text("{text}"), '
                        f'input[value*="{text}"]'
                    )
                    if btn.count() > 0 and btn.first.is_visible():
                        btn.first.click(timeout=5000)
                        return True
                except Exception:
                    continue
        return False

    @staticmethod
    def _get_body_text(page) -> str:
        parts = []
        for f in page.frames:
            try:
                el = f.query_selector("body")
                if el:
                    parts.append(el.inner_text())
            except Exception:
                continue
        return "\n".join(parts)

    async def click_answer(self, bot_id: str) -> bool:
        session = self._sessions.get(bot_id)
        if not session:
            raise RuntimeError(f"Bot {bot_id} not logged in")

        def _answer():
            return VICIdialController._click_dashboard_button(
                session.page, "ANSWER", "ACCEPT", "ANSWER CALL"
            )

        result = await self._run_on_thread(session.executor, _answer)
        if result:
            logger.info(f"Bot {bot_id} — clicked ANSWER button — audio path opened")
        else:
            logger.warning(
                f"Bot {bot_id} — ANSWER button not found — "
                f"call may already be answered or UI differs"
            )
        return result

    async def play_greeting_recording(
        self, bot_id: str, recording: str | None = None
    ) -> bool:
        session = self._sessions.get(bot_id)
        if not session:
            raise RuntimeError(f"Bot {bot_id} not logged in")

        name = recording or settings.greeting_recording

        def _play():
            return VICIdialController._click_dashboard_button(
                session.page, name
            )

        result = await self._run_on_thread(session.executor, _play)
        if result:
            logger.info(f"Bot {bot_id} — clicked '{name}' (greeting recording)")
        else:
            logger.warning(
                f"Bot {bot_id} — recording button '{name}' not found"
            )
        return result

    async def click_hangup_customer(self, bot_id: str) -> bool:
        session = self._sessions.get(bot_id)
        if not session:
            raise RuntimeError(f"Bot {bot_id} not logged in")

        def _hangup():
            return VICIdialController._click_dashboard_button(
                session.page, "HANGUP CUSTOMER", "HANGUP"
            )

        result = await self._run_on_thread(session.executor, _hangup)
        if result:
            logger.info(f"Bot {bot_id} — clicked HANGUP CUSTOMER")
        else:
            logger.warning(
                f"Bot {bot_id} — HANGUP CUSTOMER button not found"
            )
        return result

    async def click_transfer_conf(
        self, bot_id: str, transfer_number: str | None = None
    ) -> bool:
        session = self._sessions.get(bot_id)
        if not session:
            raise RuntimeError(f"Bot {bot_id} not logged in")

        num = transfer_number or settings.transfer_number or ""

        def _transfer():
            page = session.page
            clicked = VICIdialController._click_dashboard_button(
                page, "TRANSFER - CONF", "TRANSFER", "CONF"
            )
            if clicked and num:
                import time as _time
                _time.sleep(1)
                for f in page.frames:
                    try:
                        inp = f.locator(
                            'input[name="transfer_number"], '
                            'input[placeholder*="transfer"], '
                            'input[placeholder*="number"]'
                        )
                        if inp.count() > 0 and inp.first.is_visible():
                            inp.first.fill(num)
                            inp.first.press("Enter")
                            logger.info(
                                f"Bot {bot_id} — entered transfer "
                                f"number: {num}"
                            )
                            break
                    except Exception:
                        continue
            return clicked

        result = await self._run_on_thread(session.executor, _transfer)
        if result:
            logger.info(
                f"Bot {bot_id} — clicked TRANSFER - CONF"
                f"{' with number ' + num if num else ''}"
            )
        else:
            logger.warning(
                f"Bot {bot_id} — TRANSFER - CONF button not found"
            )
        return result

    async def is_on_call(self, bot_id: str) -> bool:
        session = self._sessions.get(bot_id)
        if not session:
            return False

        def _check():
            body = VICIdialController._get_body_text(session.page).upper()
            has_hangup = "HANGUP" in body or "HANGUP CUSTOMER" in body
            on_call = has_hangup and ("LIVE" in body or "CALL" in body)
            return on_call

        return await self._run_on_thread(session.executor, _check)

    async def get_body_text(self, bot_id: str) -> str:
        session = self._sessions.get(bot_id)
        if not session:
            return ""

        def _read():
            return VICIdialController._get_body_text(session.page)

        return await self._run_on_thread(session.executor, _read)

    async def restart(self, bot_id: str) -> bool:
        await self.logout(bot_id)
        await asyncio.sleep(2)
        return await self.login(bot_id)

    async def disconnect_all(self):
        async with self._lock:
            for bot_id in list(self._sessions.keys()):
                await self._logout_locked(bot_id)
