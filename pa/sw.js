// 只缓存页面本身（离线也能打开）；数据由页面自己用 ETag 管，GitHub API 请求不经过缓存。
var CACHE = "pa-shell-0.3.0";
var SHELL = ["./", "index.html", "style.css?v=0.3.0", "app.js?v=0.3.0", "manifest.webmanifest",
             "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"];

self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(SHELL); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener("fetch", function (e) {
  var url = new URL(e.request.url);
  if (url.origin !== location.origin || e.request.method !== "GET") return;
  // 先走网络（拿到新版本），断网时回落到缓存
  e.respondWith(fetch(e.request).then(function (r) {
    var copy = r.clone();
    caches.open(CACHE).then(function (c) { c.put(e.request, copy); });
    return r;
  }).catch(function () {
    return caches.match(e.request, { ignoreSearch: false }).then(function (r) { return r || caches.match("index.html"); });
  }));
});
