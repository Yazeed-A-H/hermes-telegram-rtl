"""Run: python test_rtl.py"""
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("rtl", pathlib.Path(__file__).with_name("rtl.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
t, R = m.rtl_transform, m.RLM

assert t("hello\n- a\n- b") == "hello\n- a\n- b"                       # no Arabic
assert t("```\nمرحبا\n- x\n```") == "```\nمرحبا\n- x\n```"             # code only
assert t("مرحبا\n```py\n- س\n```\nنص") == f"{R}مرحبا\n```py\n- س\n```\n{R}نص"
assert t("$$\nx = 1\n$$\nنص") == f"$$\nx = 1\n$$\n{R}نص"
assert t("- أ\n- ب\n* ج") == f"{R}1. أ\n{R}2. ب\n{R}3. ج"            # bullets
assert t("3. أ\n7. ب\n\nنص\n- ج") == f"{R}1. أ\n{R}2. ب\n\n{R}نص\n{R}1. ج"  # renumber + reset
assert t("- أ\n  - ب\n  - ج\n- د") == f"{R}1. أ\n{R}  1. ب\n{R}  2. ج\n{R}2. د"  # nested
assert t("| أ | Outlook |\n|---|---|\n| 1 |  |") == f"|{R} أ |{R} Outlook |\n|---|---|\n|{R} 1 |  |"
assert t("## عنوان\n- أ") == f"## {R}عنوان\n{R}1. أ"                   # heading, counter reset
assert t("> اقتباس") == f"> {R}اقتباس"
assert t("- [ ] مهمة\n- [x] تمت") == f"- [ ] {R}مهمة\n- [x] {R}تمت"
assert t("**اختبار**\n\n---\nنص") == f"{R}**اختبار**\n\n---\n{R}نص"
for s in ["**اختبار**\n## ع\n- أ\n- ب\n1. ج\n| أ | b |\n|--|--|\n| ت | x |\n> ق\n- [ ] م\n```\nع\n```"]:
    assert t(t(s)) == t(s)                                              # idempotent
print("ok")
