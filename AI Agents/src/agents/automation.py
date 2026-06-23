import asyncio
from collections.abc import Awaitable, Callable

from loguru import logger

from src.agents.vicidial import VICIdialController
from src.config.settings import settings


_INTEREST_KEYWORDS = [
    "transfer", "talk to someone", "talk to a person",
    "talk to agent", "talk to representative", "real person",
    "connect me", "speak to", "human",
]
_HELLO_REPEAT = ["hello hello", "hello? hello", "hellooo", "anyone there"]
_GREETING_PLAY_DURATION = 8


class AutomationAgent:

    def __init__(self):
        self.vicidial = VICIdialController()
        self._running = False
        self._poll_task: asyncio.Task | None = None
        self._monitor_tasks: dict[str, asyncio.Task] = {}
        self._call_handler_tasks: dict[str, asyncio.Task] = {}
        self._previous_statuses: dict[str, str] = {}
        self._live_callbacks: list[Callable[[str], Awaitable[None]]] = []
        self._login_tasks: dict[str, asyncio.Task] = {}
        self._login_statuses: dict[str, str] = {}
        self._login_errors: dict[str, str] = {}

    async def start(self):
        self._running = True
        logger.info("Automation Agent started")

    async def stop(self):
        self._running = False
        for bid in list(self._monitor_tasks.keys()):
            self._stop_monitoring(bid)
        for bid in list(self._call_handler_tasks.keys()):
            self._stop_call_handler(bid)
        for bid in list(self._login_tasks.keys()):
            self._login_tasks[bid].cancel()
        self._login_tasks.clear()
        if self._poll_task:
            self._poll_task.cancel()
        await self.vicidial.disconnect_all()
        logger.info("Automation Agent stopped — all VICIdial sessions closed")

    def register_live_callback(
        self, callback: Callable[[str], Awaitable[None]]
    ):
        self._live_callbacks.append(callback)

    async def login_bot(self, bot_id: str) -> bool:
        success = await self.vicidial.login(bot_id)
        if success:
            await self.vicidial.resume_agent(bot_id)
            logger.info(f"Bot {bot_id} logged in and set to READY")
            self._start_monitoring(bot_id)
        return success

    async def start_login_bot(self, bot_id: str):
        if bot_id in self._login_tasks:
            return
        self._login_statuses[bot_id] = "pending"
        self._login_errors.pop(bot_id, None)
        task = asyncio.create_task(self._login_worker(bot_id))
        self._login_tasks[bot_id] = task
        logger.info(f"[{bot_id}] Login task started (background)")

    async def _login_worker(self, bot_id: str):
        try:
            success = await self.login_bot(bot_id)
            if success:
                self._login_statuses[bot_id] = "completed"
            else:
                self._login_statuses[bot_id] = "failed"
                self._login_errors[bot_id] = "VICIdial login returned false"
        except Exception as e:
            self._login_statuses[bot_id] = "failed"
            self._login_errors[bot_id] = str(e)
            logger.error(f"[{bot_id}] Login task error: {e}")
        finally:
            self._login_tasks.pop(bot_id, None)

    def get_login_status(self, bot_id: str) -> dict:
        if bot_id in self._login_tasks:
            return {"status": "pending"}
        if bot_id in self._monitor_tasks:
            return {"status": "completed"}
        status = self._login_statuses.get(bot_id, "idle")
        result = {"status": status}
        if status == "failed":
            result["error"] = self._login_errors.get(bot_id, "Unknown error")
        return result

    async def logout_bot(self, bot_id: str):
        self._stop_monitoring(bot_id)
        self._stop_call_handler(bot_id)
        await self.vicidial.logout(bot_id)

    async def restart_bot(self, bot_id: str) -> bool:
        self._stop_monitoring(bot_id)
        self._stop_call_handler(bot_id)
        success = await self.vicidial.restart(bot_id)
        if success:
            await self.vicidial.resume_agent(bot_id)
            logger.info(f"Bot {bot_id} restarted and set to READY")
            self._start_monitoring(bot_id)
        return success

    async def pause_bot(self, bot_id: str):
        await self.vicidial.set_pause(bot_id, True)

    async def resume_bot(self, bot_id: str):
        await self.vicidial.set_pause(bot_id, False)

    async def get_bot_status(self, bot_id: str) -> str | None:
        return await self.vicidial.get_status(bot_id)

    def _start_monitoring(self, bot_id: str):
        if bot_id in self._monitor_tasks:
            return
        task = asyncio.create_task(self._monitor_worker(bot_id))
        self._monitor_tasks[bot_id] = task
        logger.info(f"[{bot_id}] Monitoring started")

    def _stop_monitoring(self, bot_id: str):
        task = self._monitor_tasks.pop(bot_id, None)
        if task:
            task.cancel()
        self._previous_statuses.pop(bot_id, None)
        logger.info(f"[{bot_id}] Monitoring stopped")

    async def _monitor_worker(self, bot_id: str):
        diag_cycles = 0
        while self._running:
            try:
                status = await self.get_bot_status(bot_id)
                prev = self._previous_statuses.get(bot_id)

                if status and status != prev:
                    self._previous_statuses[bot_id] = status
                    logger.info(
                        f"[{bot_id}] Status changed: "
                        f"{prev or 'unknown'} -> {status}"
                    )

                    status_upper = status.upper()

                    if "LIVE" in status_upper and "CALL" in status_upper:
                        logger.info(
                            f"[{bot_id}] |+|+|+ LIVE CALL DETECTED +|+|+|+"
                        )
                        sip_status = "BYPASSED" if settings.sip_bypass else "REGISTERED"
                        logger.info(
                            f"Checking SIP Media Stream: {sip_status} "
                            f"(server={settings.sip_server_ip}, "
                            f"ext={settings.sip_extension})"
                        )
                        diag_cycles = 0
                        for cb in self._live_callbacks:
                            await cb(bot_id)
                        self._start_call_handler(bot_id)

                    elif "READY" in status_upper:
                        diag_cycles = 1
                        self._stop_call_handler(bot_id)

                if status and "PAUSED" in status.upper():
                    diag_cycles = 0
                elif status and "READY" in status.upper():
                    diag_cycles += 1
                    if diag_cycles >= 30:
                        diag_cycles = 0
                        logger.info(
                            f"[{bot_id}] Still READY for 60s — "
                            f"re-checking campaign configuration"
                        )
                        await self.vicidial.diagnose_campaign(bot_id)

                await asyncio.sleep(2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[{bot_id}] Monitor error: {e}")
                await asyncio.sleep(5)

    def _start_call_handler(self, bot_id: str):
        if bot_id in self._call_handler_tasks:
            return
        task = asyncio.create_task(self._call_handler_worker(bot_id))
        self._call_handler_tasks[bot_id] = task
        logger.info(f"[{bot_id}] Call handler started")

    def _stop_call_handler(self, bot_id: str):
        task = self._call_handler_tasks.pop(bot_id, None)
        if task:
            task.cancel()
            logger.info(f"[{bot_id}] Call handler stopped")

    async def _call_handler_worker(self, bot_id: str):
        try:
            logger.info(f"[{bot_id}] Answering call...")
            await self.vicidial.click_answer(bot_id)
            await asyncio.sleep(1)

            logger.info(f"[{bot_id}] Playing greeting recording...")
            await self.vicidial.play_greeting_recording(bot_id)

            await asyncio.sleep(_GREETING_PLAY_DURATION)

            greeting_ended = asyncio.get_running_loop().time()
            response_received = False

            while self._running:
                if bot_id not in self._call_handler_tasks:
                    return

                still_on = await self.vicidial.is_on_call(bot_id)
                if not still_on:
                    logger.info(
                        f"[{bot_id}] Call ended — "
                        f"customer hung up or was disconnected"
                    )
                    await self._on_call_ended(bot_id, "customer_hungup")
                    return

                body = await self.vicidial.get_body_text(bot_id)
                body_lower = body.lower()

                if any(kw in body_lower for kw in _INTEREST_KEYWORDS):
                    logger.info(
                        f"[{bot_id}] Interest detected in body text — "
                        f"initiating transfer"
                    )
                    await self.vicidial.click_transfer_conf(bot_id)
                    await self._on_call_ended(bot_id, "transferred")
                    return

                elapsed_since_greeting = (
                    asyncio.get_running_loop().time() - greeting_ended
                )
                hello_repeat_detected = any(
                    kw in body_lower for kw in _HELLO_REPEAT
                )

                if (
                    not response_received
                    and elapsed_since_greeting > settings.silence_timeout
                ) or hello_repeat_detected:
                    if hello_repeat_detected:
                        logger.info(
                            f"[{bot_id}] 'Hello-Hello' pattern detected "
                            f"— no meaningful response, hanging up"
                        )
                    else:
                        logger.info(
                            f"[{bot_id}] No response for "
                            f"{settings.silence_timeout}s "
                            f"— hanging up"
                        )
                    await self.vicidial.click_hangup_customer(bot_id)
                    await self._on_call_ended(bot_id, "no_response")
                    return

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            logger.info(f"[{bot_id}] Call handler cancelled")
            raise
        except Exception as e:
            logger.warning(f"[{bot_id}] Call handler error: {e}")

    async def _on_call_ended(self, bot_id: str, reason: str):
        logger.info(
            f"[{bot_id}] Call ended — reason: {reason}"
        )
        self._stop_call_handler(bot_id)
        await self.vicidial.resume_agent(bot_id)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def active_bot_ids(self) -> list[str]:
        return list(self._monitor_tasks.keys())

    async def get_all_bot_statuses(self) -> dict[str, str | None]:
        result = {}
        for bot_id in self.active_bot_ids:
            result[bot_id] = await self.get_bot_status(bot_id)
        return result


automation_agent = AutomationAgent()
