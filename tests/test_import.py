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
