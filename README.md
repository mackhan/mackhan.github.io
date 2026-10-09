# mackhan.github.io

独立开发产品的发布站与更新日志。这个仓库只放网站，不放任何产品源码。

- 更新日志：`content/changelog/<产品>.md`，格式见文件顶部注释
- 产品信息与下载地址：`site.json`
- 本地预览：`python3 build.py --serve`
- 测试：`python3 -m unittest discover -s tests`
- 推送到 `main` 后，GitHub Actions 会先跑测试、再构建并发布到 https://mackhan.github.io/

应用内的「有新版本」提示读取 `https://mackhan.github.io/updates/<产品>/changelog.json`，和网页用的是同一份数据。

字体 Instrument Serif 以 SIL Open Font License 1.1 授权，见 `assets/fonts/OFL.txt`。
