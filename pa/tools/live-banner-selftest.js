var fs = require("fs");
var vm = require("vm");
var path = require("path");

var ROOT = path.join(__dirname, "..");
var appSource = fs.readFileSync(path.join(ROOT, "app.js"), "utf8");
var html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
var css = fs.readFileSync(path.join(ROOT, "style.css"), "utf8");
var COMMENT_LINE = "/" + "/";
var COMMENT_BLOCK = "/" + "*";

var passed = 0;
var failed = 0;
function check(name, cond) {
  if (cond) { passed += 1; console.log("  [PASS] " + name); }
  else { failed += 1; console.log("  [FAIL] " + name); }
}
function noForbidden(s) {
  var words = ["批准", "允许", "拒绝", "审批", "点此回复", "立即回复", "去回复", "点击回复", "同意并", "驳回"];
  var i;
  for (i = 0; i < words.length; i += 1) {
    if (s.indexOf(words[i]) >= 0) return false;
  }
  return true;
}
function noInteractions(s) {
  var bad = ["<button", "<a ", "<a>", "onclick", "addEventListener", "href",
             "role=\"button\"", "tabindex", "<form", "window.open", "location."];
  var i;
  for (i = 0; i < bad.length; i += 1) {
    if (s.indexOf(bad[i]) >= 0) return false;
  }
  return true;
}
function noop() {}
function makeElement() {
  var e = {
    hidden: false,
    textContent: "",
    value: "",
    disabled: false,
    className: "",
    style: {},
    dataset: {},
    children: [],
    classList: { toggle: noop, add: noop, remove: noop },
    addEventListener: noop,
    appendChild: function (c) { e.children.push(c); return c; },
    replaceChildren: function () { e.children = []; },
    setAttribute: noop,
    querySelectorAll: function () { return []; },
    closest: function () { return null; },
    onclick: null
  };
  return e;
}
var els = {};
var documentStub = {
  getElementById: function (id) {
    if (!els[id]) els[id] = makeElement();
    return els[id];
  },
  createElement: function () { return makeElement(); },
  querySelectorAll: function () { return []; },
  addEventListener: noop
};
var windowStub = { addEventListener: noop, scrollTo: noop };
function FakeEncoder() {}
FakeEncoder.prototype.encode = function () { return new Uint8Array(0); };
function FakeDecoder() {}
FakeDecoder.prototype.decode = function () { return ""; };
var sandbox = {
  window: windowStub,
  document: documentStub,
  location: { hash: "", pathname: "/pa/", search: "", origin: "https://example.test", reload: noop },
  history: { replaceState: noop, pushState: noop, back: noop },
  localStorage: { getItem: function () { return null; }, setItem: noop, removeItem: noop },
  navigator: {},
  TextEncoder: FakeEncoder,
  TextDecoder: FakeDecoder,
  atob: function () { return ""; },
  fetch: function () { return Promise.resolve(); },
  confirm: function () { return false; },
  console: console
};

console.log("[LiveBanner 静态守卫] 读取 pa/ 源码并用 Node 桩加载 app.js");
try {
  vm.runInNewContext(appSource, sandbox, { filename: "app.js" });
} catch (err) {
  console.log("  [FAIL] app.js 无法在 Node 桩中加载：" + err.message);
  process.exit(1);
}
var pa = windowStub.__pa;

check("window.__pa.liveAlerts 已暴露为函数", typeof pa.liveAlerts === "function");
check("window.__pa.renderLive 已暴露为函数", typeof pa.renderLive === "function");

var d = pa.liveAlerts([{ project: "P1", state: "deciding" }]);
check("deciding → count 1 / visible true", d.count === 1 && d.visible === true);
check("deciding 文案沿用「等你决策」", d.items[0].label === "等你决策");
check("waiting 文案沿用「等你回复」", pa.liveAlerts([{ project: "P", state: "waiting" }]).items[0].label === "等你回复");
check("六档之外的状态不算需关注", pa.liveAlerts([{ project: "P", state: "failure" }]).visible === false);

var mix = pa.liveAlerts([
  { project: "A", state: "deciding" },
  { project: "B", state: "waiting" },
  { project: "C", state: "working" },
  { project: "D", state: "active" },
  { project: "E", state: "open" },
  { project: "F", state: "off" }
]);
check("混合状态只保留 deciding/waiting（生成中等不算需关注）", mix.count === 2 && mix.visible === true);
check("混合状态逐条项目名正确", mix.items[0].project === "A" && mix.items[1].project === "B");
check("空列表 → count 0 / visible false（横幅隐藏）", pa.liveAlerts([]).count === 0 && pa.liveAlerts([]).visible === false);
check("undefined → 隐藏（无 live 数据不报错）", pa.liveAlerts(undefined).visible === false);
check("null → 隐藏（无 live 数据不报错）", pa.liveAlerts(null).visible === false);
check("仅 working/active/open/off → 隐藏", pa.liveAlerts([
  { project: "A", state: "working" },
  { project: "B", state: "active" },
  { project: "C", state: "open" },
  { project: "D", state: "off" }
]).visible === false);
check("liveAlerts 为纯函数，不修改入参", (function () {
  var input = [{ project: "A", state: "deciding" }];
  pa.liveAlerts(input);
  return input.length === 1 && input[0].state === "deciding" && input[0].project === "A";
})());

pa.renderLive([{ project: "甲", state: "deciding" }, { project: "乙", state: "waiting" }]);
check("有关注会话时 #live 横幅显示", els["live"].hidden === false);
check("标题为「2 个会话在等你」", els["live-head"].textContent === "2 个会话在等你");
var rendered = els["live-list"].children.map(function (c) { return c.textContent; });
check("逐条列出「项目名 · 状态」", rendered.length === 2 && rendered[0] === "甲 · 等你决策" && rendered[1] === "乙 · 等你回复");
check("渲染出的文案不含禁用词", noForbidden(els["live-head"].textContent + rendered.join("")));
pa.renderLive([]);
check("无关注会话时 #live 横幅隐藏", els["live"].hidden === true);
pa.renderLive([{ project: "丙", state: "deciding" }, { project: "丁", state: "waiting" }, { project: "戊", state: "deciding" }]);
check("3 条关注时标题为「3 个会话在等你」", els["live-head"].textContent === "3 个会话在等你");

var css = fs.readFileSync(path.join(ROOT, "..", "pa", "style.css"), "utf8");
check("[hidden] 有兜底规则，横幅能真正隐藏", /\[hidden\][^{]*\{[^}]*display:\s*none[^}]*!important/.test(css));
var hs = html.indexOf("<div class=\"live-banner\"");
var he = html.indexOf("<div class=\"kpis\">", hs);
var bannerHtml = hs >= 0 && he > hs ? html.slice(hs, he) : "";
check("index.html 存在横幅容器 id=live", bannerHtml.indexOf("id=\"live\"") >= 0);
check("横幅初始 hidden（默认不显示）", bannerHtml.indexOf("hidden") >= 0);
check("横幅含红点 live-dot", bannerHtml.indexOf("live-dot") >= 0);
check("横幅含标题 live-head", bannerHtml.indexOf("live-head") >= 0);
check("横幅含列表 live-list", bannerHtml.indexOf("live-list") >= 0);
check("横幅 DOM 无任何 button/链接/点击处理器/跳转", noInteractions(bannerHtml));
check("横幅 DOM 无 HTML 注释", bannerHtml.indexOf("<!--") < 0);
check("横幅 DOM 文案不含禁用词", noForbidden(bannerHtml));
check("横幅区未引入第三方脚本/外链", bannerHtml.indexOf("<script") < 0 && bannerHtml.indexOf("http") < 0);

var cs = appSource.indexOf("var LIVE_LABEL");
var ce = appSource.indexOf("function render(b)");
var liveCode = cs >= 0 && ce > cs ? appSource.slice(cs, ce) : "";
check("app.js 抽出可单测纯函数 liveAlerts + 渲染 renderLive",
      liveCode.indexOf("function liveAlerts") >= 0 && liveCode.indexOf("function renderLive") >= 0);
check("render() 调用 renderLive(b.live && b.live.projects)",
      appSource.indexOf("renderLive(b.live && b.live.projects)") >= 0);
check("沿用既有 window.__pa 测试钩子暴露纯函数",
      appSource.indexOf("window.__pa = {") >= 0 && appSource.indexOf("window.__pa.liveAlerts = liveAlerts;") >= 0);
check("横幅渲染代码无 innerHTML / 点击处理器 / 链接 / 按钮",
      noInteractions(liveCode) && liveCode.indexOf("innerHTML") < 0);
check("横幅 DOM 文本一律走 el()/fill() 的 textContent",
      (liveCode.indexOf("textContent") >= 0 || liveCode.indexOf("fill(") >= 0) && liveCode.indexOf("el(") >= 0);
check("新增 app.js 代码无注释（行注释与块注释）",
      liveCode.indexOf(COMMENT_LINE) < 0 && liveCode.indexOf(COMMENT_BLOCK) < 0);
check("新增 app.js 文案不含禁用词", noForbidden(liveCode));
check("「N 个会话在等你」标题文案存在", liveCode.indexOf("个会话在等你") >= 0);

var cssNew = css.indexOf(".live-banner") >= 0 ? css.slice(css.indexOf(".live-banner")) : "";
check("style.css 有横幅与红点样式", cssNew.indexOf(".live-banner") >= 0 && cssNew.indexOf(".live-dot") >= 0);
check("红点为纯 CSS 圆点（border-radius 50%）", cssNew.indexOf("border-radius: 50%") >= 0);
check("红点/横幅沿用现有 CSS 变量（暗色主题自适应）",
      cssNew.indexOf("var(--err)") >= 0 && cssNew.indexOf("var(--accent-soft)") >= 0 && cssNew.indexOf("var(--accent)") >= 0);
check("style.css 全文无持续脉冲动画（@keyframes/animation/infinite/pulse）",
      css.indexOf("@keyframes") < 0 && css.indexOf("animation:") < 0 && css.indexOf("infinite") < 0 && css.indexOf("pulse") < 0);
check("新增 CSS 无注释、无 @import、不引入第三方",
      cssNew.indexOf(COMMENT_BLOCK) < 0 && cssNew.indexOf("@import") < 0 && cssNew.indexOf("http") < 0);
check("未引入系统通知权限（app.js 无 Notification）",
      appSource.indexOf("Notification") < 0 && liveCode.indexOf("location") < 0 && liveCode.indexOf("window.open") < 0);

console.log("");
console.log("[LiveBanner] " + (passed + failed) + " 条断言 / " + passed + " 通过 / " + failed + " 失败");
if (failed > 0) process.exit(1);
