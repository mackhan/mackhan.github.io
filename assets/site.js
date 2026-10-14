// 语言切换：记住用户的选择，之后中文页不再按浏览器语言自动跳到英文
document.addEventListener("click", function (ev) {
  var a = ev.target.closest && ev.target.closest("a[data-lang]");
  if (a) { try { localStorage.setItem("siteLang", a.dataset.lang); } catch (e) {} }
});

// 更新日志页：按产品筛选（URL 里带 ?p=kvmini 可直接分享筛选结果）
(function () {
  var f = document.getElementById("filter");
  if (!f) return;
  function set(k) {
    f.querySelectorAll("button").forEach(function (b) { b.classList.toggle("on", b.dataset.k === k); });
    document.querySelectorAll(".entry").forEach(function (e) { e.hidden = k !== "all" && e.dataset.p !== k; });
    document.querySelectorAll(".prod").forEach(function (p) { p.classList.toggle("on", p.dataset.k === k); });
    var u = new URL(location.href);
    if (k === "all") u.searchParams.delete("p"); else u.searchParams.set("p", k);
    history.replaceState(null, "", u);
  }
  f.addEventListener("click", function (ev) { var b = ev.target.closest("button"); if (b) set(b.dataset.k); });
  var p = new URL(location.href).searchParams.get("p");
  if (p && f.querySelector('[data-k="' + p + '"]')) set(p);
})();
