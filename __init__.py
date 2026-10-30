"""telegram-rtl: Arabic replies go out as rich messages with InputRichMessage.is_rtl.

Tested on Telegram for iOS: rich + is_rtl right-anchors headings, real bullets, numbering, tables and
quote text; Telegram also accepts editMessageText(rich_message + is_rtl) on a plain streamed preview.
Text that never goes rich (clarify cards, approvals, prompts, rich-refused or >32k replies) passes through
format_message, which gets RLM lines via rtl_transform so it is right-aligned too.
Temporary workaround: delete this plugin once Hermes emits is_rtl itself.
Tests: test_rtl.py (python3), test_patch.py (Hermes interpreter, see its docstring).
"""
import functools
import logging

from .rtl import _AR, _code_mask, rtl_transform

logger = logging.getLogger("telegram-rtl")


def _ar(text):
    """True when Arabic is >= 30% of the letters outside code blocks, so an English message that only
    names one Arabic word stays LTR."""
    if not isinstance(text, str) or not _AR.search(text):
        return False
    lines = text.split("\n")
    letters = [ch for l, code in zip(lines, _code_mask(lines)) if not code for ch in l if ch.isalpha()]
    return bool(letters) and sum(1 for ch in letters if _AR.match(ch)) / len(letters) >= 0.3


def _patch(cls):
    names = ("_rich_message_payload", "_needs_rich_rendering", "format_message")
    missing = [n for n in names if not callable(getattr(cls, n, None))]
    if missing:
        logger.warning("TelegramAdapter missing %s; telegram-rtl inactive", missing)
        return
    if getattr(cls._rich_message_payload, "_telegram_rtl", False):
        return

    payload, needs, fmt = cls._rich_message_payload, cls._needs_rich_rendering, cls.format_message

    @functools.wraps(payload)
    def _rich_message_payload(self, content, *a, **k):
        out = payload(self, content, *a, **k)
        if _ar(content):
            out["is_rtl"] = True
            logger.debug("telegram-rtl: rich message sent with is_rtl")
        return out

    @functools.wraps(needs)
    def _needs_rich_rendering(self, content):
        return _ar(content) or needs(self, content)  # Arabic always takes the rich path

    @functools.wraps(fmt)
    def format_message(self, content):
        if _ar(content):
            try:
                # MarkdownV2 text: clarify cards, approvals, prompts, and replies that could not go rich.
                content = rtl_transform(content)
                logger.debug("telegram-rtl: MarkdownV2 text sent with RLM lines")
            except Exception:
                logger.warning("rtl_transform failed; sending original text", exc_info=True)
        return fmt(self, content)

    for f in (_rich_message_payload, _needs_rich_rendering, format_message):
        f._telegram_rtl = True
        setattr(cls, f.__name__, f)
    logger.info("telegram-rtl active (is_rtl) on %s.%s", cls.__module__, cls.__name__)


def register(ctx):
    # The bundled telegram adapter is imported lazily under a loader-chosen module name, so importing it
    # here would patch a different class copy. Patch the class of the instance the registry really builds.
    try:
        from gateway.platform_registry import platform_registry as reg
        orig = reg.create_adapter
        if getattr(orig, "_telegram_rtl", False):
            return

        @functools.wraps(orig)
        def create_adapter(name, config):
            adapter = orig(name, config)
            if name == "telegram" and adapter is not None:
                try:
                    _patch(type(adapter))
                except Exception as exc:
                    logger.warning("telegram-rtl inactive: %s", exc)
            return adapter

        create_adapter._telegram_rtl = True
        reg.create_adapter = create_adapter
    except Exception as exc:
        logger.warning("telegram-rtl inactive: cannot hook platform_registry: %s", exc)
