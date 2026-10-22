import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import import_changelog as I  # noqa: E402

RUST = r'''
fn get_changelog() -> Vec<ChangelogEntry> {
    vec![
        ChangelogEntry {
            version: "1.0.2".to_string(),
            date: "2026-07-07".to_string(),
            changes: vec![
                "🐛 修复 Office 里粘贴失败".to_string(),
                "✨ 新增 \"快速模式\"".to_string(),
                "🧪 新增 4 项单测".to_string(),
                "🔧 【BUG-052 修复】重写 FFI 调用".to_string(),
            ],
            changes_en: vec![],
        },
        ChangelogEntry {
            version: "1.0.1".to_string(),
            date: "2026-07-01".to_string(),
            changes: vec![
                "🧪 只有测试".to_string(),
            ],
            changes_en: vec![],
        },
        ChangelogEntry {
            version: "0.9.0".to_string(),
            date: "2026-04-01".to_string(),
            changes: vec![
                "✨ 上架前版本".to_string(),
            ],
            changes_en: vec![],
        },
    ]
}
'''


class TestImport(unittest.TestCase):
    def test_parse_and_unescape(self):
        es = I.parse_rust(RUST)
        self.assertEqual([e["version"] for e in es], ["1.0.2", "1.0.1", "0.9.0"])
        self.assertIn('新增 "快速模式"', es[0]["items"][1])

    def test_internal_filter_is_case_sensitive_whole_word(self):
        self.assertEqual(I.classify("snipscribe", "🐛 修复 Office 里粘贴失败")[0], "修复")
        self.assertIsNone(I.classify("snipscribe", "🔧 重写 FFI 调用")[0])
        self.assertIsNone(I.classify("kvmini", "新增诊断日志")[0])

    def test_markdown_rules(self):
        md, st = I.to_markdown("snipscribe", I.parse_rust(RUST))
        self.assertIn("## v1.0.2 · 2026-07-07", md)
        self.assertIn("### 新功能\n- 新增 \"快速模式\"", md)
        self.assertNotIn("1.0.1", md)          # 过滤后为空的版本不出现
        self.assertNotIn("0.9.0", md)          # SnipScribe 上架前的版本不导入
        self.assertEqual(st["dropped"], 3)

    def test_simplify_strips_technical_details(self):
        self.assertEqual(
            I.simplify("修复 Windows 主控端撞屏幕边缘即断连（P0）：cursor grab 用滞后的 GetCursorInfo 复核"),
            "修复 Windows 主控端撞屏幕边缘即断连")
        self.assertEqual(
            I.simplify("修复方括号键左右颠倒（真实 kVK_ANSI_LeftBracket=33）"), "修复方括号键左右颠倒")
        self.assertEqual(I.simplify("新增 StateGuard 模块：Watchdog 每 500ms 检测"), "")
        self.assertEqual(I.simplify("i18n 新增 4 条 key"), "")
        # 真实产品名不算代码标识符
        self.assertIn("BetterTouchTool", I.simplify("Mac 上 Logitech Options / BetterTouchTool 等映射继续生效"))
        # 普通括号说明保留
        self.assertEqual(I.simplify("文件接收目录可自定义（留空 = 系统「下载」）"), "文件接收目录可自定义（留空 = 系统「下载」）")

    def test_kvmini_verb_grouping_and_note(self):
        self.assertEqual(I.classify("kvmini", "修复滚轮无反应")[0], "修复")
        self.assertEqual(I.classify("kvmini", "新增鼠标侧键设置")[0], "新功能")
        self.assertEqual(I.classify("kvmini", "传输加密仍在开发中：请只在可信网络中使用")[0], "note")


if __name__ == "__main__":
    unittest.main()


SWIFT = r'''
enum AppChangelog {
    static let entries: [ChangelogEntry] = [
        ChangelogEntry(
            version: "1.1.0",
            date: "2026-10-20",
            changes: [
                "新增主屏小组件",
                "修复「我的」页得分条顶满",
            ],
            changesEn: [
                "New Home Screen widgets",
                "Fixed score bars appearing full",
            ]),
    ]
}
'''


class SwiftTest(unittest.TestCase):
    def test_parse_swift_entries(self):
        e = I.parse_swift(SWIFT)
        self.assertEqual(len(e), 1)
        self.assertEqual((e[0]["version"], e[0]["date"]), ("1.1.0", "2026-10-20"))
        self.assertEqual(e[0]["items"], ["新增主屏小组件", "修复「我的」页得分条顶满"])
        self.assertEqual(e[0]["items_en"], ["New Home Screen widgets", "Fixed score bars appearing full"])

    def test_english_follows_chinese_grouping(self):
        body, _ = I.to_markdown("lifetree", I.parse_swift(SWIFT), "en")
        self.assertIn("### New\n- New Home Screen widgets", body)
        self.assertIn("### Fixed\n- Fixed score bars appearing full", body)

    def test_lifetree_items_are_kept_as_is(self):
        """生命树的 App 内条目本身就是用户语言，不做术语过滤"""
        body, st = I.to_markdown("lifetree", I.parse_swift(SWIFT), "zh")
        self.assertEqual(st["dropped"], 0)
        self.assertIn("新增主屏小组件", body)


RUST_EN = r'''
fn get_changelog() -> Vec<ChangelogEntry> {
    vec![
        ChangelogEntry {
            version: "1.0.3".to_string(),
            date: "2026-08-01".to_string(),
            changes: vec![
                "新增暗色模式".to_string(),
            ],
            changes_en: vec![
                "New dark mode".to_string(),
            ],
        },
    ]
}
'''

SWIFT_NO_EN = r'''
        ChangelogEntry(
            version: "1.0.1",
            date: "2026-10-01",
            changes: [
                "新增主屏小组件",
            ]),
'''


class RustEnglishTest(unittest.TestCase):
    """Rust 源也要能出英文草稿（--lang en / both）"""

    def test_parse_rust_keeps_english(self):
        self.assertEqual(I.parse_rust(RUST_EN)[0]["items_en"], ["New dark mode"])

    def test_english_draft_has_content(self):
        body, st = I.to_markdown("kvmini", I.parse_rust(RUST_EN), "en")
        self.assertEqual(st["kept"], 1)
        self.assertIn("### New\n- New dark mode", body)


class SwiftWithoutEnglishTest(unittest.TestCase):
    """老版本还没补 changesEn 时，中文条目不能跟着一起消失"""

    def test_chinese_items_survive(self):
        e = I.parse_swift(SWIFT_NO_EN)
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0]["items"], ["新增主屏小组件"])
        self.assertEqual(e[0]["items_en"], [])
