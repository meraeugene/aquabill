self.addEventListener("install", function (e) {
  console.log("Service Worker: Installed");
  e.waitUntil(
    caches.open("waterbilling-cache").then(function (cache) {
      return cache.addAll([
        "/",
        "/static/css/style.css", // Add your CSS/JS here
      ]);
    })
  );
});

self.addEventListener("fetch", function (e) {
  e.respondWith(
    caches.match(e.request).then(function (response) {
      return response || fetch(e.request);
    })
  );
});
