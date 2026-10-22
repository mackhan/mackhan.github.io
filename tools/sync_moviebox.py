#!/usr/bin/env python3
"""同步 MovieBox 的对外门面清单（等价于 tools/sync_product.py moviebox）。

清单由 MovieBox 发布时生成在自己的 GitHub Pages 上，SSOT 是它的 package.json（版本）
与 pages/changelog.html（日期与更新摘要）：

    https://mackhan.github.io/MovieBox/manifest.json

注意：MovieBox 的清单只有中文更新内容（changelog），英文条目要人工补到
content/changelog/en/moviebox.md，否则首页构建会因中英不一致失败。

用法：
    python3 tools/sync_moviebox.py            # 拉取并同步
    python3 tools/sync_moviebox.py --check    # 只对比，不写文件（CI 用）
    python3 tools/sync_moviebox.py --local ~/Documents/Git/MovieBox/pages/manifest.json
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_product import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(default_pid="moviebox"))
