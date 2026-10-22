// PromptLedger 手机端：从 GitHub 私有仓库拉取电脑上传的加密数据包，在本机用 WebCrypto 解密后显示。
//
// - 配对：扫电脑上的二维码 → 打开 …/pa/#p=<base64url({r: 仓库, t: 只读令牌, k: 密钥})>
//   「#」后面的内容浏览器不会发给任何服务器；读到后存进本机 localStorage，并立刻从地址栏抹掉。
// - 数据：仓库里每台电脑一个分支 dev-<设备名>，分支里只有一个 bundle.json（AES-256-GCM 密文）。
// - 只在打开和下拉刷新时拉取；带 ETag 条件请求，没变化时 GitHub 返回 304，不下载也不算额度。
(function () {
  "use strict";
  var VERSION = "0.4.0";
  var AAD = new TextEncoder().encode("prompt-archive/v1");   // 协议标识沿用旧名，与电脑端 sync.rs 一致
  var CFG_KEY = "pa.cfg", CACHE_KEY = "pa.cache";
  var $ = function (id) { return document.getElementById(id); };

  // ---------- 工具 ----------
  function fmt(n) {
    n = Number(n) || 0;
    if (n >= 1e8) return (n / 1e8).toFixed(2) + "亿";
    if (n >= 1e4) return (n / 1e4).toFixed(1) + "万";
    return String(n);
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;   // 一律 textContent：提示词原文不当 HTML 解析
    return e;
  }
  function fill(id, items, render, emptyText) {
    var ul = $(id);
    ul.replaceChildren();
    if (!items || !items.length) { ul.appendChild(el("li", "empty", emptyText)); return; }
    items.forEach(function (x) { ul.appendChild(render(x)); });
  }
  function b64ToBytes(s) {
    s = s.replace(/-/g, "+").replace(/_/g, "/");
    while (s.length % 4) s += "=";
    var bin = atob(s), out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function banner(msg, isErr) {
    var b = $("banner");
    b.textContent = msg || "";
    b.hidden = !msg;
    b.classList.toggle("err", !!isErr);
  }
  function load(key, dflt) {
    try { return JSON.parse(localStorage.getItem(key)) || dflt; } catch (e) { return dflt; }
  }
  function save(key, v) { localStorage.setItem(key, JSON.stringify(v)); }

  // ---------- 配对 ----------
  function readPairing() {
    var m = /[#&]p=([A-Za-z0-9_-]+)/.exec(location.hash);
    if (!m) return;
    try {
      var p = JSON.parse(new TextDecoder().decode(b64ToBytes(m[1])));
      if (!/^[\w.-]+\/[\w.-]+$/.test(p.r) || b64ToBytes(p.k).length !== 32) throw new Error("bad");
      // 令牌可以为空：仓库公开时直接读密文，不需要凭证。分支优先用二维码里带的。
      save(CFG_KEY, { repo: p.r, token: p.t || "", key: p.k, branch: p.d || "" });
      localStorage.removeItem(CACHE_KEY);
      banner("配对成功。建议现在「添加到主屏幕」，以后从桌面图标打开。");
    } catch (e) {
      banner("配对链接无效，请在电脑上重新生成二维码", true);
    }
    history.replaceState(null, "", location.pathname + location.search);   // 抹掉地址栏里的密钥
  }

  // ---------- 拉取与解密 ----------
  function gh(cfg, path, etag) {
    var headers = { "Accept": "application/vnd.github.raw+json", "X-GitHub-Api-Version": "2022-11-28" };
    if (cfg.token) headers["Authorization"] = "Bearer " + cfg.token;
    if (etag) headers["If-None-Match"] = etag;
    return fetch("https://api.github.com/repos/" + cfg.repo + path, { headers: headers, cache: "no-store" });
  }
  // 公开仓库走 raw：不带令牌、不占 API 配额（未登录只有 60 次/小时，多刷几次就没了）
  function raw(cfg, br, etag) {
    var headers = { "Accept": "application/vnd.github.raw+json" };
    if (etag) headers["If-None-Match"] = etag;
    // 带一个时间戳参数：raw 的 CDN 会缓存旧文件，不带的话刚同步完手机还看到上一版
    return fetch("https://raw.githubusercontent.com/" + cfg.repo + "/" + br + "/bundle.json?_=" + Date.now(),
                 { headers: headers, cache: "no-store" });
  }
  function apiError(r) {
    if (r.status === 401) return "令牌无效或已过期：请在电脑上换一个只读令牌，重新配对";
    if (r.status === 403 || r.status === 404) return "令牌没有读取同步仓库的权限，或仓库不存在（" + r.status + "）";
    return "GitHub 返回 " + r.status;
  }

  function fetchAll(cfg) {
    var cache = load(CACHE_KEY, {});
    var listed = cfg.branch ? Promise.resolve([{ name: cfg.branch }])
      : gh(cfg, "/branches?per_page=100").then(function (r) {
          if (!r.ok) throw new Error(apiError(r));
          return r.json();
        });
    return listed.then(function (branches) {
      var names = branches.map(function (b) { return b.name; }).filter(function (n) { return /^dev-/.test(n); });
      if (!names.length) throw new Error("仓库里还没有数据：在电脑托盘 App 的设置里点「立即同步」");
      return Promise.all(names.map(function (name) {
        var c = cache[name] || {};
        var get = cfg.token
          ? gh(cfg, "/contents/bundle.json?ref=" + encodeURIComponent(name), c.etag)
          : raw(cfg, name, c.etag);
        return get.then(function (r) {
          if (r.status === 304 && c.body) return c;
          if (!r.ok) throw new Error(apiError(r));
          return r.text().then(function (body) { return { etag: r.headers.get("ETag"), body: body }; });
        }).then(function (entry) { return [name, entry]; });
      }));
    }).then(function (pairs) {
      var next = {};
      pairs.forEach(function (p) { next[p[0]] = p[1]; });
      save(CACHE_KEY, next);
      return next;
    });
  }

  function decryptOne(keyB64, body) {
    var env = JSON.parse(body);
    if (env.v !== 1 || env.alg !== "AES-256-GCM") throw new Error("数据格式版本不支持，请更新手机页面");
    return crypto.subtle.importKey("raw", b64ToBytes(keyB64), "AES-GCM", false, ["decrypt"]).then(function (key) {
      return crypto.subtle.decrypt({ name: "AES-GCM", iv: b64ToBytes(env.iv), additionalData: AAD, tagLength: 128 },
                                   key, b64ToBytes(env.ct));
    }).then(function (plain) {
      var b = JSON.parse(new TextDecoder().decode(plain));
      b._device = env.device;
      return b;
    }, function () { throw new Error("解密失败：密钥不匹配，请重新配对"); });
  }

  function decryptAll(cfg, cache) {
    return Promise.all(Object.keys(cache).map(function (k) { return decryptOne(cfg.key, cache[k].body); }));
  }

  // ---------- 多台电脑合并 ----------
  var NUM = ["turns", "requests", "total_tokens", "fresh_input", "output_tokens"];
  function addNums(a, b) { NUM.forEach(function (k) { a[k] = (a[k] || 0) + (b[k] || 0); }); return a; }
  // 合并规则只有三条，别混着用：
  //   ① 可相加 —— 按天的用量、每个项目的轮次 / Token。两台机做的是不同的会话，加起来才是对的
  //   ② 只能取最新 —— 额度（账号级，两台机读到同一份）、代码行数（同一份仓库两台机各有一份副本，
  //      数出来是同一个数，相加就翻倍，所以取 max）
  //   ③ 按仓库归并 —— 同一个项目在 Mac 上是 /Users/.../X、在 Windows 上是 C:\...\X，
  //      靠快照里带的 repo（git remote 规范化）把两边认成同一个项目；没有 repo 就退回用项目名
  var PADD = ["week_turns", "week_tokens", "d30_turns", "d30_tokens"];

  function mergeDay(a, b) {                        // 把 b 那天的账并进 a
    NUM.forEach(function (k) { a[k] = (a[k] || 0) + (b[k] || 0); });
    var mergeMap = function (dst, src) {
      Object.keys(src || {}).forEach(function (k) {
        var t = dst[k] || (dst[k] = { turns: 0, total_tokens: 0 });
        t.turns += (src[k] || {}).turns || 0;
        t.total_tokens += (src[k] || {}).total_tokens || 0;
      });
    };
    mergeMap(a.clients, b.clients);
    mergeMap(a.projects, b.projects);
  }

  function merge(bundles) {
    bundles.sort(function (a, b) { return a.built_at < b.built_at ? 1 : -1; });   // 最新的在前
    var base = JSON.parse(JSON.stringify(bundles[0]));
    var s = base.snapshot;

    // ---- 按天 / 按月明细：这是唯一「没有保质期」的事实，窗口全部由手机自己按今天的日期算 ----
    // days = 上月 1 号起（整月边界），months = 更早的整月。两者不重叠，相加即得任意窗口。
    var byDay = {};
    (s.days || []).forEach(function (d) { byDay[d.day] = JSON.parse(JSON.stringify(d)); });
    var byMonth = {};
    (s.months || []).forEach(function (m) { byMonth[m.month] = JSON.parse(JSON.stringify(m)); });

    // ---- 项目：父项合计 + 子项按机器分开 ----
    var proj = {};
    var order = [];
    function parentOf(p) {
      var key = p.repo || ("name:" + p.name);
      var t = proj[key];
      if (!t) {
        t = proj[key] = { name: p.name, repo: p.repo || "", week_turns: 0, week_tokens: 0,
                          d30_turns: 0, d30_tokens: 0, last_active: p.last_active || "",
                          recent: p.recent, loc: p.loc, devices: [] };
        order.push(key);
      }
      return t;
    }
    function addProject(p, dev) {
      var t = parentOf(p);
      PADD.forEach(function (k) { t[k] += p[k] || 0; });
      if ((p.last_active || "") > t.last_active) { t.last_active = p.last_active; t.recent = p.recent; }
      // 代码行数：同一份仓库各台机数出来是同一个数 → 取最大的那份，绝不相加
      if (p.loc && (!t.loc || (p.loc.code || 0) > (t.loc.code || 0))) t.loc = p.loc;
      t.devices.push({ device: dev, name: p.name, week_turns: p.week_turns || 0, week_tokens: p.week_tokens || 0,
                       d30_turns: p.d30_turns || 0, d30_tokens: p.d30_tokens || 0,
                       last_active: p.last_active || "", loc: p.loc, recent: p.recent });
    }
    (s.projects || []).forEach(function (p) { addProject(p, bundles[0]._device); });
    var allTime = s.all_time;

    bundles.slice(1).forEach(function (b) {
      var o = b.snapshot;
      ["all_time"].forEach(function (k) { if (o[k]) addNums(s[k] || (s[k] = {}), o[k]); });
      if (o.d30) {
        s.d30 = s.d30 || { total_tokens: 0, start: o.d30.start, unassigned_tokens: 0 };
        s.d30.total_tokens += o.d30.total_tokens || 0;
        s.d30.unassigned_tokens += o.d30.unassigned_tokens || 0;
      }
      // 额度是账号级的：多台电脑读到的是同一份，取最新的那次
      if (o.quota && (!s.quota || (o.quota.fetchedAt || 0) > (s.quota.fetchedAt || 0))) s.quota = o.quota;
      // 代码行数同理：同一份仓库各台机数出来是同一个数，取最新的那台（bundles[0]）即可，绝不相加
      if (o.loc && !s.loc) s.loc = o.loc;
      (o.days || []).forEach(function (d) {
        if (!byDay[d.day]) byDay[d.day] = JSON.parse(JSON.stringify(d));
        else mergeDay(byDay[d.day], d);
      });
      (o.months || []).forEach(function (m) {
        if (!byMonth[m.month]) byMonth[m.month] = JSON.parse(JSON.stringify(m));
        else mergeDay(byMonth[m.month], m);
      });
      (o.last7 || []).forEach(function (d) {
        var t = s.last7.filter(function (x) { return x.day === d.day; })[0];
        if (t) { t.turns += d.turns; t.total_tokens += d.total_tokens; }
      });
      (o.projects || []).forEach(function (p) {
        var t = parentOf(p);
        PADD.forEach(function (k) { t[k] += p[k] || 0; });
        if ((p.last_active || "") > t.last_active) { t.last_active = p.last_active; t.recent = p.recent; }
        if (p.loc && (!t.loc || (p.loc.code || 0) > (t.loc.code || 0))) t.loc = p.loc;
        t.devices.push({ device: b._device, name: p.name, week_turns: p.week_turns || 0, week_tokens: p.week_tokens || 0,
                         d30_turns: p.d30_turns || 0, d30_tokens: p.d30_tokens || 0,
                         last_active: p.last_active || "", loc: p.loc, recent: p.recent });
      });
      s.repeats = (s.repeats || []).concat(o.repeats || []);
      base.prompts = (base.prompts || []).concat(b.prompts || []);
      var have = {};
      base.manuals.forEach(function (m) { have[m.project + "/" + m.name] = 1; });
      (b.manuals || []).forEach(function (m) { if (!have[m.project + "/" + m.name]) base.manuals.push(m); });
    });

    s.days = Object.keys(byDay).sort().map(function (k) { return byDay[k]; });
    s.months = Object.keys(byMonth).sort().map(function (k) { return byMonth[k]; });
    s.projects = order.map(function (k) { return proj[k]; });
    s.projects.sort(function (a, b) { return b.week_turns - a.week_turns || b.d30_turns - a.d30_turns; });
    s.all_time = allTime || s.all_time;
    base._devices = bundles.map(function (x) { return x._device; });
    return base;
  }

  // 从按天明细算出某个窗口的合计（窗口由手机自己按 today_date 划，不信任电脑端算好的聚合值——
  // 那是有保质期的：一台机三天没开，它那包里的「今日」是三天前的，直接相加就把今天算虚高了）
  function sumDays(days, since, until) {
    var o = { turns: 0, requests: 0, total_tokens: 0, fresh_input: 0, output_tokens: 0,
              clients: {}, projects: {} };
    (days || []).forEach(function (d) {
      if (since && d.day < since) return;
      if (until && d.day > until) return;
      NUM.forEach(function (k) { o[k] += d[k] || 0; });
      ["clients", "projects"].forEach(function (g) {
        Object.keys(d[g] || {}).forEach(function (k) {
          var t = o[g][k] || (o[g][k] = { turns: 0, total_tokens: 0 });
          t.turns += (d[g][k] || {}).turns || 0;
          t.total_tokens += (d[g][k] || {}).total_tokens || 0;
        });
      });
    });
    return o;
  }

  // ISO 日期 → 那个周的周一。
  // 必须全程用 UTC 算：如果按本地时区解析、再用 toISOString() 输出，东八区会把周一定到前一天（周日）。
  // 固定取当天 12:00Z，这样地球上任何时区都不会因为换算跨到另一天。
  function mondayOf(iso) {
    var d = new Date(iso + "T12:00:00Z");
    var w = (d.getUTCDay() + 6) % 7;             // 周一=0
    d.setUTCDate(d.getUTCDate() - w);
    return d.toISOString().slice(0, 10);
  }
  function todayISO() {                          // 本机「今天」，不能用 UTC（东八区早上 8 点前会算成昨天）
    var d = new Date(), p = function (n) { return String(n).padStart(2, "0"); };
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
  }

  // 把一整月并进窗口合计（months 里的月份都是 days 覆盖不到的更早整月，不会重复算）
  function addMonth(o, m) {
    NUM.forEach(function (k) { o[k] += m[k] || 0; });
    ["clients", "projects"].forEach(function (g) {
      Object.keys(m[g] || {}).forEach(function (k) {
        var t = o[g][k] || (o[g][k] = { turns: 0, total_tokens: 0 });
        t.turns += (m[g][k] || {}).turns || 0;
        t.total_tokens += (m[g][k] || {}).total_tokens || 0;
      });
    });
  }

  function sumRange(days, months, since, until) {
    var o = sumDays(days, since, until);
    (months || []).forEach(function (m) {
      if (m.month + "-31" < since.slice(0, 7) + "-01") return;   // 整月都在窗口之前
      if (m.month + "-01" > until) return;                       // 整月都在窗口之后
      addMonth(o, m);
    });
    return o;
  }

  // 四个窗口：今日 / 本周 / 本月 / 本年。
  // 全部由手机按 days（按天）+ months（整月）自己划；只有旧包（没有 days）才退回电脑端算好的聚合值。
  function windows(s) {
    var t = s.today_date || todayISO();
    var since = { today: t, week: mondayOf(t), month: t.slice(0, 8) + "01", year: t.slice(0, 4) + "-01-01" };
    var d = s.days, m = s.months;
    if (!d || !d.length) {
      return { from: "agg", since: since, today: s.today || {}, week: s.week || {},
               month: s.month || {}, year: s.year || {} };
    }
    return { from: "detail", since: since,
             today: sumRange(d, m, since.today, t), week: sumRange(d, m, since.week, t),
             month: sumRange(d, m, since.month, t), year: sumRange(d, m, since.year, t) };
  }

  // 按天明细里存的是客户端 id（codebuddy），显示要换成名字
  var CLIENT_NAME = { workbuddy: "WorkBuddy", codebuddy: "CodeBuddy", cursor: "Cursor", claude: "Claude Code",
                      codex: "Codex", gemini: "Gemini CLI", trae: "Trae", opencode: "OpenCode",
                      kiro: "Kiro", cline: "Cline" };
  function cname(id) {
    if (!id) return "未归类";
    return CLIENT_NAME[id] || id.charAt(0).toUpperCase() + id.slice(1);
  }

  // ---------- 简易 Markdown（先整体转义，再只加我们自己的标签，所以不会注入 HTML） ----------
  function esc(s) { return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;"); }
  function inline(s) {
    return esc(s)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
      .replace(/\[([^\]]+)\]\((https:\/\/[^)\s]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  }
  function markdown(src) {
    var lines = (src || "").replace(/\r/g, "").split("\n"), out = [], i = 0;
    while (i < lines.length) {
      var l = lines[i];
      if (/^```/.test(l)) {
        var code = [];
        for (i++; i < lines.length && !/^```/.test(lines[i]); i++) code.push(lines[i]);
        out.push("<pre><code>" + esc(code.join("\n")) + "</code></pre>"); i++; continue;
      }
      var h = /^(#{1,4})\s+(.*)$/.exec(l);
      if (h) { var n = Math.min(h[1].length, 3); out.push("<h" + n + ">" + inline(h[2]) + "</h" + n + ">"); i++; continue; }
      if (/^\s*\|.*\|\s*$/.test(l)) {
        var rows = [];
        for (; i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i]); i++) rows.push(lines[i]);
        var html = "<div class=\"tbl\"><table>";
        rows.forEach(function (r, idx) {
          if (/^\s*\|[\s:|-]+\|\s*$/.test(r)) return;
          var cells = r.trim().replace(/^\||\|$/g, "").split("|");
          var tag = idx === 0 ? "th" : "td";
          html += "<tr>" + cells.map(function (c) { return "<" + tag + ">" + inline(c.trim()) + "</" + tag + ">"; }).join("") + "</tr>";
        });
        out.push(html + "</table></div>"); continue;
      }
      if (/^\s*([-*]|\d+\.)\s+/.test(l)) {
        var ordered = /^\s*\d+\./.test(l), items = [];
        for (; i < lines.length && /^\s*([-*]|\d+\.)\s+/.test(lines[i]); i++) items.push(lines[i].replace(/^\s*([-*]|\d+\.)\s+/, ""));
        var t = ordered ? "ol" : "ul";
        out.push("<" + t + ">" + items.map(function (x) { return "<li>" + inline(x) + "</li>"; }).join("") + "</" + t + ">"); continue;
      }
      if (/^>\s?/.test(l)) {
        var q = [];
        for (; i < lines.length && /^>\s?/.test(lines[i]); i++) q.push(inline(lines[i].replace(/^>\s?/, "")));
        out.push("<blockquote>" + q.join("<br>") + "</blockquote>"); continue;
      }
      if (/^\s*(---|\*\*\*)\s*$/.test(l)) { out.push("<hr>"); i++; continue; }
      if (!l.trim()) { i++; continue; }
      var para = [];
      for (; i < lines.length && lines[i].trim() && !/^(#{1,4}\s|```|\s*\||\s*([-*]|\d+\.)\s|>)/.test(lines[i]); i++) para.push(inline(lines[i]));
      out.push("<p>" + para.join("<br>") + "</p>");
    }
    return out.join("\n");
  }

  // ---------- 渲染 ----------
  function kpis(prefix, s) {
    $(prefix + "-turns").textContent = s.turns;
    $(prefix + "-tokens").textContent = fmt(s.total_tokens);
    $(prefix + "-fresh").textContent = fmt(s.fresh_input);
    $(prefix + "-out").textContent = fmt(s.output_tokens);
  }
  function pct(n, total) {
    if (!total) return "";
    var v = n * 100 / total;
    return (v >= 10 || v === 0 ? Math.round(v) : v.toFixed(1)) + "%";
  }
  function clientRow(c) {
    var li = el("li");
    li.appendChild(el("span", "grow", c.name));
    li.appendChild(el("span", "tag", c.turns + " 轮 · " + (c.token_tracked ? fmt(c.total_tokens) + " Token" : "本地无 Token 记录")));
    if (c.token_tracked && c.total_tokens) li.appendChild(el("span", "pct", (c.share || 0) + "%"));
    return li;
  }
  // 按天明细里只有客户端 id 和项目名，这里补上显示名并排序
  function fillClients(id, map, total, empty) {
    var rows = Object.keys(map || {}).map(function (k) { return { k: k, v: map[k] }; })
      .sort(function (a, b) { return b.v.total_tokens - a.v.total_tokens || b.v.turns - a.v.turns; })
      .filter(function (x) { return x.v.turns || x.v.total_tokens; });
    fill(id, rows, function (x) {
      var li = el("li");
      li.appendChild(el("span", "grow", cname(x.k)));
      li.appendChild(el("span", "tag", x.v.turns + " 轮 · " + fmt(x.v.total_tokens) + " Token"));
      if (total) li.appendChild(el("span", "pct", pct(x.v.total_tokens, total)));
      return li;
    }, empty);
  }
  function fillProjects(id, map, total, empty) {
    var rows = Object.keys(map || {}).map(function (k) { return { k: k, v: map[k] }; })
      .sort(function (a, b) { return b.v.total_tokens - a.v.total_tokens || b.v.turns - a.v.turns; })
      .filter(function (x) { return x.v.turns; })
      .slice(0, 12);
    fill(id, rows, function (x) { return projStatRow(x.k, x.v, total); }, empty);
  }
  // 代码行数：各台电脑数的是同一份仓库 → 电脑端已经取过最新的一份，这里只显示
  function renderLoc(s) {
    var l = s.loc || {};
    $("k-loc").textContent = l.code ? fmt(l.code) : "–";
    [["today", "k-loc-today"], ["week", "k-loc-week"], ["month", "k-loc-month"], ["year", "k-loc-year"]]
      .forEach(function (kv) { $(kv[1]).textContent = "+" + fmt((l[kv[0]] || {}).add || 0); });
  }
  // 本月额度：电脑端读到后随数据包一起发过来，这里只显示（金额和百分比都在电脑端算好）
  function money(n) {
    var parts = (Number(n) || 0).toFixed(2).split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return parts.join(".");
  }
  function pct1(n) {
    var v = Number(n) || 0;
    return (v % 1 === 0 ? String(v) : v.toFixed(1)) + "%";
  }
  function ago(ts) {
    var s = Math.max(0, Math.floor(Date.now() / 1000 - (Number(ts) || 0)));
    if (s < 60) return "刚刚";
    if (s < 3600) return Math.floor(s / 60) + " 分钟前";
    if (s < 86400) return Math.floor(s / 3600) + " 小时前";
    return Math.floor(s / 86400) + " 天前";
  }
  function renderQuota(s) {
    var box = $("quota");
    box.replaceChildren();
    var q = s.quota || {};
    if (!q.ok) return;                         // 电脑上没读到就不占地方
    var used = Number(q.usagePercent) || 0, left = Number(q.remainingPercent) || 0;
    var low = left <= 15;
    box.appendChild(el("div", "qh", "本月额度 · 来自额度面板"));
    var top = el("div", "qbig");
    top.appendChild(el("b", "qnum" + (low ? " low" : ""), pct1(used)));
    top.appendChild(el("small", "", low ? "已用 · 快用完了" : "已用"));
    box.appendChild(top);
    var bar = el("div", "qbar"), seg = el("span", low ? "low" : "");
    seg.style.width = Math.min(100, used) + "%";
    bar.appendChild(seg);
    box.appendChild(bar);
    box.appendChild(el("div", "qmeta", "¥" + money(q.usedCny) + " / ¥" + money(q.quotaCny)
      + " · 剩余 ¥" + money(q.remainingCny) + "（" + pct1(left) + "）"));
    box.appendChild(el("div", "qmeta", [q.user, q.dailyUsedCny ? "今日 ¥" + money(q.dailyUsedCny) : "",
      (q.stale ? "上次取到 " : "") + ago(q.fetchedAt)].filter(Boolean).join(" · ")));
    if (q.resetAt) {
      var gap = Number(q.shortDays) > 0;
      box.appendChild(el("div", "qplan" + (gap ? " warn" : ""),
        "重置 " + shortTime(q.resetAt) + "（" + day1(q.resetInDays) + " 天后）"
        + (q.exhaustAt ? " · 日均 ¥" + money(q.avgDailyCny) + "，预计 " + shortTime(q.exhaustAt) + " 耗尽"
            + (gap ? "，空窗 " + day1(q.shortDays) + " 天" : "") : "")));
    }
  }
  function shortTime(x) {
    var m = /(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(x || "");
    return m ? m[2] + "-" + m[3] + " " + m[4] + ":" + m[5] : (x || "");
  }
  function day1(n) { return (Number(n) || 0).toFixed(1); }
  // 30 天各项目 Token 占比条（前 5 个 + 其他 + 未归类）
  var SHARE_COLORS = ["#ff9f43", "#5b8def", "#34c759", "#af52de", "#ff6b81"];
  function renderShare(s) {
    var box = $("share");
    box.replaceChildren();
    var d = s.d30 || {}, total = d.total_tokens || 0;
    if (!total) return;
    var ps = (s.projects || []).filter(function (p) { return p.d30_tokens; })
      .sort(function (a, b) { return b.d30_tokens - a.d30_tokens; });
    var segs = ps.slice(0, 5).map(function (p, i) { return { name: p.name, n: p.d30_tokens, color: SHARE_COLORS[i] }; });
    var rest = ps.slice(5).reduce(function (a, p) { return a + p.d30_tokens; }, 0);
    if (rest) segs.push({ name: "其他", n: rest, color: "var(--dim)" });
    if (d.unassigned_tokens) segs.push({ name: "未归类", n: d.unassigned_tokens, color: "var(--line)" });
    box.appendChild(el("div", "share-h", "最近 30 天 Token · 共 " + fmt(total)));
    var bar = el("div", "share-bar");
    segs.forEach(function (x) {
      var seg = el("span");
      seg.style.width = (x.n * 100 / total) + "%";
      seg.style.background = x.color;
      bar.appendChild(seg);
    });
    box.appendChild(bar);
    var lg = el("div", "share-legend");
    segs.forEach(function (x) {
      var it = el("span"), dot = el("i");
      dot.style.background = x.color;
      it.appendChild(dot);
      it.appendChild(document.createTextNode(x.name + " " + pct(x.n, total)));
      lg.appendChild(it);
    });
    box.appendChild(lg);
  }
  // 项目页的卡片：父项 = 各台电脑合并后的合计；点开「N 台电脑」看每台机各自的数字
  function devName(d) { return (d || "").replace(/^dev-/, "") || "这台电脑"; }
  function projectCard(p) {
    var li = el("li"), head = el("div", "head");
    head.appendChild(el("span", "name", p.name));
    head.appendChild(el("span", "nums",
      "本周 " + p.week_turns + " 轮 · 30 天 " + p.d30_turns + " 轮 · " + fmt(p.d30_tokens)));
    li.appendChild(head);
    if (p.recent && p.recent.length) {
      var r = el("div", "recent");
      p.recent.forEach(function (t) { r.appendChild(el("div", "", t)); });
      li.appendChild(r);
    }
    var l = p.loc;
    if (l && l.code) {
      var langs = (l.langs || []).slice(0, 2).map(function (x) { return x.name; }).join("、");
      li.appendChild(el("div", "tag", "代码 " + fmt(l.code) + " 行 · " + l.files + " 个文件" + (langs ? " · " + langs : "")));
    }
    if (p.last_active) li.appendChild(el("div", "tag", "最近活动 " + p.last_active));

    var devs = (p.devices || []).slice().sort(function (a, b) { return b.d30_turns - a.d30_turns; });
    if (devs.length > 1) {
      var btn = el("button", "more", devs.length + " 台电脑 ›");
      var sub = el("ul", "subs");
      sub.hidden = true;
      btn.onclick = function () {
        sub.hidden = !sub.hidden;
        btn.classList.toggle("on", !sub.hidden);
        btn.textContent = devs.length + " 台电脑 " + (sub.hidden ? "›" : "⌄");
      };
      devs.forEach(function (d) {
        var row = el("li"), top = el("div", "dline");
        top.appendChild(el("span", "dname", devName(d.device)));
        top.appendChild(el("span", "dnums", "本周 " + d.week_turns + " 轮 · 30 天 " + d.d30_turns
          + " 轮 · " + fmt(d.d30_tokens)));
        row.appendChild(top);
        row.appendChild(el("div", "dnums", "最近活动 " + (d.last_active || "–")
          + (d.loc && d.loc.code ? " · 代码 " + fmt(d.loc.code) + " 行" : "")));
        sub.appendChild(row);
      });
      li.appendChild(btn);
      li.appendChild(sub);
    } else if (devs.length === 1) {
      li.appendChild(el("div", "tag", devName(devs[0].device)));
    }
    return li;
  }
  // 今日 / 本周 / 本月 / 本年页里的「按项目」：来自按天明细，只有轮次和 Token
  function projStatRow(name, v, total) {
    var li = el("li");
    li.appendChild(el("span", "grow", name));
    li.appendChild(el("span", "tag", v.turns + " 轮 · " + fmt(v.total_tokens) + " Token"));
    if (total) li.appendChild(el("span", "pct", pct(v.total_tokens, total)));
    return li;
  }
  function openDoc(title, md) {
    $("reader-title").textContent = title;
    $("reader-body").innerHTML = markdown(md);
    $("main").hidden = true; $("tabs").hidden = true; $("reader").hidden = false;
    window.scrollTo(0, 0);
    history.pushState({ reader: 1 }, "");
  }
  function closeDoc() { $("reader").hidden = true; $("main").hidden = false; $("tabs").hidden = false; }

  var searchIndex = [];
  function renderSearch() {
    var q = ($("s-q").value || "").trim().toLowerCase();
    var box = $("s-results");
    box.replaceChildren();
    if (!searchIndex.length) {
      box.appendChild(el("li", "empty", "这台电脑还没同步提示词索引（电脑端升级后同步一次即可）"));
      return;
    }
    if (q.length < 2) {
      box.appendChild(el("li", "empty", "输入两个字以上，在 " + searchIndex.length + " 条历史提示词里搜"));
      return;
    }
    var hit = searchIndex.filter(function (x) {
      return (x.t + " " + x.p).toLowerCase().indexOf(q) >= 0;
    }).slice(0, 80);
    if (!hit.length) { box.appendChild(el("li", "empty", "没有匹配的提示词")); return; }
    hit.forEach(function (x) {
      var li = el("li");
      li.appendChild(el("span", "grow", x.t));
      li.appendChild(el("span", "tag", (x.d || "").slice(5) + " · " + (x.p || "未归类")));
      box.appendChild(li);
    });
    if (hit.length === 80) box.appendChild(el("li", "empty", "只显示前 80 条，再输入几个字缩小范围"));
  }

  function render(b) {
    searchIndex = (b.prompts || []).slice();
    if (b.live && b.live.projects) {                  // 状态跃迁时电脑会立刻推一次，手机上是新鲜的
      $("live").textContent = b.live.projects.filter(function (x) { return x.state === "working" || x.state === "waiting" || x.state === "deciding"; })
        .map(function (x) { return x.project + " " + ({ working: "生成中", waiting: "等响应", deciding: "等决策" }[x.state] || x.state); })
        .join(" · ");
    }
    var s = b.snapshot;
    var W = windows(s), t = W.since.today;
    kpis("t", W.today); kpis("w", W.week); kpis("m", W.month); kpis("y", W.year);
    $("w-range").textContent = W.since.week + " ~ " + t + "（周一至今）";
    $("m-range").textContent = W.since.month + " ~ " + t + "（本月 1 号至今）";
    $("y-range").textContent = W.since.year + " ~ " + t + "（今年 1 月 1 号至今）";

    var max = Math.max.apply(null, s.last7.map(function (d) { return d.total_tokens; }).concat([1]));
    var bars = $("bars");
    bars.replaceChildren();
    s.last7.forEach(function (d, i) {
      var bar = el("div", "bar" + (i === s.last7.length - 1 ? " today" : ""));
      var col = el("span");
      col.style.height = Math.round(d.total_tokens * 100 / max) + "%";
      bar.appendChild(col);
      bar.appendChild(el("small", "", d.day.slice(5).replace("-", "/")));
      bars.appendChild(bar);
    });

    renderQuota(s);
    renderShare(s);
    renderLoc(s);
    if (W.from === "agg") {          // 旧包：没有按天明细，只能用电脑端算好的那份
      fill("t-clients", (s.clients || {}).today.filter(function (c) { return c.turns || c.total_tokens; }), clientRow, "今天还没有记录");
    } else {
      fillClients("t-clients", W.today.clients, W.today.total_tokens, "今天还没有记录");
    }
    ["week", "month", "year"].forEach(function (k) {
      var p = k.charAt(0);                       // week→w / month→m / year→y
      fillClients(p + "-clients", W[k].clients, W[k].total_tokens,
                  ({ week: "本周", month: "本月", year: "今年" })[k] + "还没有记录");
      fillProjects(p + "-projects", W[k].projects, W[k].total_tokens,
                   ({ week: "本周", month: "本月", year: "今年" })[k] + "还没有项目活动");
    });
    fill("repeats", s.repeats, function (r) {
      var li = el("li");
      li.appendChild(el("span", "count", "×" + r.count));
      li.appendChild(el("span", "grow", r.sample));
      li.appendChild(el("span", "tag", r.projects.join("、")));
      return li;
    }, "本周没有重复提问");
    fill("projects", s.projects, projectCard, "最近 30 天没有项目活动");
    fill("reports", b.reports, function (r) {
      var li = el("li");
      li.appendChild(el("a", "grow", r.week + " 周报"));
      li.onclick = function () { openDoc(r.week + " 周报", r.markdown); };
      return li;
    }, "还没有周报（每周一 09:00 在电脑上自动生成）");
    fill("manuals", b.manuals, function (m) {
      var li = el("li");
      li.appendChild(el("a", "grow", m.project + " · " + m.name));
      li.onclick = function () { openDoc(m.project + " · " + m.name, m.markdown); };
      return li;
    }, "还没有项目手册");

    var t = new Date(b.built_at);
    var devs = b._devices ? b._devices.length + " 台电脑" : (b._device || "");
    $("updated").textContent = "数据 " + t.toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) +
      (devs ? " · " + devs : "");
  }

  // ---------- 主流程 ----------
  function showPaired(paired) {
    $("pair").hidden = paired;
    $("tabs").hidden = !paired; $("main").hidden = !paired;
    $("refresh").hidden = !paired; $("unpair").hidden = !paired;
  }

  function refresh() {
    var cfg = load(CFG_KEY, null);
    showPaired(!!cfg);
    if (!cfg) return Promise.resolve();
    $("refresh").disabled = true;
    var cache = load(CACHE_KEY, {});
    var fromCache = Object.keys(cache).length
      ? decryptAll(cfg, cache).then(function (bs) { render(merge(bs)); }).catch(function () {})
      : Promise.resolve();
    return fromCache.then(function () { return fetchAll(cfg); })
      .then(function (fresh) { return decryptAll(cfg, fresh); })
      .then(function (bs) { render(merge(bs)); if (!/配对成功/.test($("banner").textContent)) banner(""); })
      .catch(function (e) {
        var offline = !navigator.onLine || /fetch|network|Load failed/i.test(String(e.message));
        banner(offline ? "离线：显示的是上次的数据" : e.message, !offline);
      })
      .then(function () { $("refresh").disabled = false; });
  }

  $("s-q").addEventListener("input", renderSearch);
  $("tabs").addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (!b) return;
    document.querySelectorAll(".tabs button").forEach(function (x) { x.classList.toggle("on", x === b); });
    document.querySelectorAll(".tab").forEach(function (x) { x.hidden = x.id !== "tab-" + b.dataset.tab; });
  });
  $("refresh").onclick = refresh;
  $("reader-back").onclick = function () { history.back(); };
  window.addEventListener("popstate", closeDoc);
  $("unpair").onclick = function () {
    if (!confirm("解除配对会删除这台手机上保存的密钥和缓存数据，确定吗？")) return;
    localStorage.removeItem(CFG_KEY); localStorage.removeItem(CACHE_KEY);
    location.reload();
  };
  document.addEventListener("visibilitychange", function () { if (!document.hidden) refresh(); });
  $("version").textContent = "v" + VERSION;

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(function () {});
  readPairing();
  refresh();

  window.__pa = { markdown: markdown, merge: merge, decryptOne: decryptOne,   // 给自动化测试用
                  windows: windows, sumRange: sumRange, render: render, projectCard: projectCard };
})();
