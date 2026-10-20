# mackhan.github.io

独立开发产品的发布站与更新日志。这个仓库只放网站，不放任何产品源码。

- 更新日志：`content/changelog/<产品>.md`，格式见文件顶部注释
- 英文更新日志：`content/changelog/en/<产品>.md`，必须覆盖中文版的每个版本（版本号与日期一致），否则构建失败
- 多语言：中文在根目录，英文在 `/en/`；`site.json` 的英文文案用 `<字段>_en`（`lead_en`、`desc_en`、`note_en`、`name_en`、`platforms_en`、`label_en`）。中文页在浏览器语言不是中文、且用户没手动选过语言时跳到英文页；新增语言在 `build.py` 的 `LANGS` 里加一组
- 原样发布的静态页：`content/static/<路径>`（如 `KVMini/privacy-policy/index.html`）
- 产品信息与下载地址：`site.json`
- 从应用内更新日志生成草稿：`python3 tools/import_changelog.py <产品> <Rust 源文件>`，输出到 `drafts/`（不入库），改写后再并入 `content/changelog/`
- 本地预览：`python3 build.py --serve`
- 测试：`python3 -m unittest discover -s tests`
- 推送到 `main` 后，GitHub Actions 会先跑测试、再构建并发布到 https://mackhan.github.io/

应用内的「有新版本」提示读取 `https://mackhan.github.io/updates/<产品>/changelog.json`，和网页用的是同一份数据。

## 文档

- `docs/账户与管理后台.md`：注册登录、管理员统计 / 权限页的设计方案（账户体系待拍板；管理员后台 P0 已上线：<https://mackhan.github.io/pa-admin/>）
- 站点总体方案（服务器、收款、激活）：工作区 `release-site-design.md`（不在本仓库）
- 使用统计聚合：`stats.py`（读私有埋点仓 `mackhan/pa-stats` 的 JSONL，只输出聚合数字），测试 `tests/test_stats.py`

字体 Instrument Serif 以 SIL Open Font License 1.1 授权，见 `assets/fonts/OFL.txt`。
