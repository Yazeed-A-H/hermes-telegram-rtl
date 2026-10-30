# telegram-rtl

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin that shows Telegram replies right to left for Arabic and other right-to-left languages written in Arabic script, such as Persian and Urdu.

Telegram rich messages have an `is_rtl` flag that right-aligns the whole message, including headings, bullets, numbered lists, tables and quotes. Hermes does not set this flag yet, so replies in these languages show up left-aligned with list markers on the wrong side.

> [!WARNING]
> This plugin is a temporary workaround. It modifies Hermes core behavior at runtime by wrapping internal methods of the Telegram adapter, since Hermes has no public plugin hook for the outgoing Telegram message. A Hermes update can change those internals without notice. Use the plugin until Hermes supports `is_rtl` natively through an upstream fix, then remove it.

## What it does

- Sends a reply as a rich message with `is_rtl: true` when at least 30% of its letters outside code blocks are in Arabic script. An English reply that quotes one Arabic word stays left to right.
- Leaves code and math blocks untouched, so code stays left-aligned.
- When a reply cannot go out as a rich message (approval prompts, clarify cards, replies Telegram rejects as rich, very long replies), it falls back to MarkdownV2, puts a right-to-left mark (U+200F) at the start of each line and turns bullets into numbered items.

Detection uses the Arabic Unicode blocks.

## Tested on

- Hermes Agent 0.22.5 on macOS
- Telegram for iOS

Other operating systems and Telegram clients have not been tested.

## Requirements

- Hermes Agent 0.22.5 or newer
- The Telegram gateway

## Install

```bash
hermes plugins install Yazeed-A-H/hermes-telegram-rtl --enable
hermes gateway restart
```

The plugin attaches to the Telegram adapter when the gateway creates it, so the gateway has to restart.

To install an exact version, pin the full commit SHA:

```bash
hermes plugins install Yazeed-A-H/hermes-telegram-rtl --ref <40-character-commit-sha> --enable
```

In Hermes Desktop, go to **Capabilities → Plugins → Install from Git** and enter `Yazeed-A-H/hermes-telegram-rtl`, or open this link:

```
hermes://plugin/install?repo=Yazeed-A-H/hermes-telegram-rtl&enable=1
```

## Check that it is active

After the restart, the agent log should contain:

```
telegram-rtl active (is_rtl) on ...TelegramAdapter
```

```bash
grep "telegram-rtl" ~/.hermes/logs/agent.log | tail -3
```

If the log shows `telegram-rtl inactive` or `TelegramAdapter missing`, the plugin could not attach and replies go out unchanged.

## Tests

```bash
cd ~/.hermes/plugins/telegram-rtl
python3 test_rtl.py
"$(hermes --print-runtime-command | python3 -c 'import json,sys;print(json.load(sys.stdin)[0])')" test_patch.py
```

`test_rtl.py` checks the MarkdownV2 fallback rewrite. `test_patch.py` loads the real Telegram adapter class from your Hermes install and checks the patch against it, without starting the gateway or using the network. Both print `ok`.

## After updating Hermes

Run `test_patch.py` after every `hermes update`. The plugin depends on three internal methods of the Telegram adapter (`_rich_message_payload`, `_needs_rich_rendering`, `format_message`) and on `platform_registry.create_adapter`. If an update removes them, the plugin logs a warning and leaves replies unchanged. If an update changes how they behave, the test fails and shows which check broke.

## Limitations

- Because it wraps Hermes internals instead of using a public hook, it fails the `no core override` check in `hermes plugins validate` and cannot be listed in the Hermes plugin catalog.
- It works on Telegram only.

## Removing it

Once Hermes sets `is_rtl` itself, uninstall the plugin:

```bash
hermes plugins remove telegram-rtl
hermes gateway restart
```

## License

MIT
