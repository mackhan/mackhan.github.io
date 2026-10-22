#!/usr/bin/env python3
"""同步 KVMini 的对外门面清单（等价于 tools/sync_product.py kvmini）。

清单由 KVMini 发布时生成并随 Release 分发，SSOT 是它的 Cargo.toml（版本）
与 src-tauri/src/main.rs 的 get_changelog()（日期 + 中英文更新内容）：

    https://github.com/mackhan/KVMini/releases/latest/download/manifest.json

用法：
    python3 tools/sync_kvmini.py                     # 拉取并同步
    python3 tools/sync_kvmini.py --check             # 只对比，不写文件
    python3 tools/sync_kvmini.py --all               # 连历史缺失版本一起补
    python3 tools/sync_kvmini.py --local ~/Documents/Git/KVMini/pages/manifest.json
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_product import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(default_pid="kvmini"))
