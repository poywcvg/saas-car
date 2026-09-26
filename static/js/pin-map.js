/*
 * pin-map.js — نقشه‌ی سبک و بدون وابستگی برای لوکیشن مغازه (کاشی‌های OpenStreetMap).
 *
 * الگوی «سوزن ثابت، نقشه متحرک»: سوزن همیشه وسط است و کاربر نقشه را زیرش می‌کشد؛
 * برای کاربر کم‌سواد ساده‌تر از کشیدن خودِ سوزن است.
 *
 *   var map = PinMap.create(el, { lat, lng, zoom, interactive, onStart, onMove });
 *   map.setView(lat, lng, zoom); map.zoomBy(+1); map.getCenter();
 *   PinMap.parseLink("https://maps.google.com/...@30.28,57.08,17z")  → {lat, lng} | null
 *
 * نقشه‌های ثابت (ویترین/صفحه‌ی مشتری) خودکار ساخته می‌شوند:
 *   <div class="pm-map" data-pin-map data-lat=".." data-lng=".." data-zoom="16"></div>
 */
(function () {
  "use strict";

  var TILE = 256;
  var MIN_Z = 4;
  var MAX_Z = 19;
  var TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";

  function clampZ(z) {
    return Math.max(MIN_Z, Math.min(MAX_Z, Math.round(z)));
  }

  function worldSize(z) {
    return TILE * Math.pow(2, z);
  }

  function project(lat, lng, z) {
    var s = worldSize(z);
    var sin = Math.sin((lat * Math.PI) / 180);
    sin = Math.min(Math.max(sin, -0.9999), 0.9999);
    return {
      x: ((lng + 180) / 360) * s,
      y: (0.5 - Math.log((1 + sin) / (1 - sin)) / (4 * Math.PI)) * s,
    };
  }

  function unproject(x, y, z) {
    var s = worldSize(z);
    var n = Math.PI - (2 * Math.PI * y) / s;
    return {
      lat: (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n))),
      lng: (x / s) * 360 - 180,
    };
  }

  function create(el, opts) {
    opts = opts || {};
    var interactive = opts.interactive !== false;
    var z = clampZ(opts.zoom || 13);
    var c = project(+opts.lat || 0, +opts.lng || 0, z);
    var tiles = {};
    var raf = 0;
    var ghost = null;
    var ghostTimer = 0;

    var layer = document.createElement("div");
    layer.className = "pm-layer";
    el.insertBefore(layer, el.firstChild);
    el.setAttribute("dir", "ltr");

    var attr = document.createElement("a");
    attr.className = "pm-attr";
    attr.href = "https://www.openstreetmap.org/copyright";
    attr.target = "_blank";
    attr.rel = "noopener";
    attr.textContent = "© OpenStreetMap";
    el.appendChild(attr);

    function clampCenter() {
      var s = worldSize(z);
      c.x = ((c.x % s) + s) % s;
      c.y = Math.max(0, Math.min(s, c.y));
    }

    function render() {
      raf = 0;
      var w = el.clientWidth;
      var h = el.clientHeight;
      if (!w || !h) return;
      var n = Math.pow(2, z);
      var left = c.x - w / 2;
      var top = c.y - h / 2;
      var x0 = Math.floor(left / TILE);
      var x1 = Math.floor((left + w) / TILE);
      var y0 = Math.max(0, Math.floor(top / TILE));
      var y1 = Math.min(n - 1, Math.floor((top + h) / TILE));
      var seen = {};
      // لایه‌ی قبلی هم همراهِ کشیدن جابه‌جا شود
      if (ghost) {
        ghost.style.transform =
          "translate(" + Math.round(ghost.pmCx - c.x) + "px," + Math.round(ghost.pmCy - c.y) + "px) " + ghost.pmBase;
      }

      for (var tx = x0; tx <= x1; tx++) {
        for (var ty = y0; ty <= y1; ty++) {
          var key = z + "/" + tx + "/" + ty;
          seen[key] = true;
          var img = tiles[key];
          if (!img) {
            img = new Image();
            img.className = "pm-tile";
            img.alt = "";
            img.draggable = false;
            img.decoding = "async";
            img.onload = function () {
              this.classList.add("pm-in");
              if (ghost) maybeDropGhost();
            };
            img.src = TILE_URL.replace("{z}", z)
              .replace("{x}", ((tx % n) + n) % n)
              .replace("{y}", ty);
            tiles[key] = img;
            layer.appendChild(img);
          }
          img.style.transform =
            "translate3d(" + Math.round(tx * TILE - left) + "px," + Math.round(ty * TILE - top) + "px,0)";
        }
      }
      for (var k in tiles) {
        if (!seen[k]) {
          tiles[k].remove();
          delete tiles[k];
        }
      }
    }

    function schedule() {
      if (!raf) raf = requestAnimationFrame(render);
    }

    function center() {
      var p = unproject(c.x, c.y, z);
      return { lat: +p.lat.toFixed(6), lng: +p.lng.toFixed(6), zoom: z };
    }

    function changed() {
      if (opts.onMove) opts.onMove(center());
    }

    function dropGhost() {
      clearTimeout(ghostTimer);
      if (ghost) ghost.remove();
      ghost = null;
    }

    function maybeDropGhost() {
      for (var k in tiles) {
        if (!tiles[k].complete) return;
      }
      dropGhost();
    }

    // کاشی‌های زوم فعلی را بزرگ/کوچک‌شده نگه می‌دارد تا کاشی‌های زوم تازه برسند
    function keepGhost(px, py, f) {
      dropGhost();
      ghost = layer;
      ghost.className = "pm-layer pm-ghost";
      ghost.pmBase = "translate(" + px + "px," + py + "px) scale(" + f + ") translate(" + -px + "px," + -py + "px)";
      ghost.style.transform = ghost.pmBase;
      layer = document.createElement("div");
      layer.className = "pm-layer";
      ghost.after(layer);
      tiles = {};
      ghostTimer = setTimeout(dropGhost, 2500);
    }

    // بزرگ‌نمایی حولِ یک نقطه‌ی صفحه (همان نقطه زیر انگشت/موس می‌ماند)
    function zoomAround(px, py, dz) {
      var nz = clampZ(z + dz);
      if (nz === z) return;
      var w = el.clientWidth;
      var h = el.clientHeight;
      var f = Math.pow(2, nz - z);
      keepGhost(px, py, f);
      var wx = (c.x - w / 2 + px) * f;
      var wy = (c.y - h / 2 + py) * f;
      z = nz;
      c.x = wx - (px - w / 2);
      c.y = wy - (py - h / 2);
      clampCenter();
      ghost.pmCx = c.x;
      ghost.pmCy = c.y;
      render();
      changed();
    }

    function zoomBy(dz) {
      zoomAround(el.clientWidth / 2, el.clientHeight / 2, dz);
    }

    function setView(lat, lng, zoom) {
      dropGhost();
      if (zoom) z = clampZ(zoom);
      c = project(+lat, +lng, z);
      clampCenter();
      render();
      changed();
    }

    if (interactive) {
      var pointers = {};
      var pinchBase = 0;
      var dragging = false;

      var local = function (e) {
        var r = el.getBoundingClientRect();
        return { x: e.clientX - r.left, y: e.clientY - r.top };
      };
      var ids = function () {
        return Object.keys(pointers);
      };
      var spread = function () {
        var k = ids();
        var a = pointers[k[0]];
        var b = pointers[k[1]];
        return Math.hypot(a.x - b.x, a.y - b.y);
      };

      el.addEventListener("pointerdown", function (e) {
        if (e.target === attr) return;
        if (e.button && e.button !== 0) return;
        el.setPointerCapture(e.pointerId);
        pointers[e.pointerId] = local(e);
        if (ids().length === 2) pinchBase = spread();
        if (!dragging) {
          dragging = true;
          el.classList.add("pm-dragging");
          if (opts.onStart) opts.onStart();
        }
      });

      el.addEventListener("pointermove", function (e) {
        var prev = pointers[e.pointerId];
        if (!prev) return;
        var now = local(e);
        var count = ids().length;
        // با دو انگشت، نصفِ حرکت هر انگشت = حرکت میانگین
        c.x -= (now.x - prev.x) / count;
        c.y -= (now.y - prev.y) / count;
        pointers[e.pointerId] = now;
        clampCenter();
        if (count === 2 && pinchBase) {
          var ratio = spread() / pinchBase;
          if (ratio > 1.6 || ratio < 0.6) {
            var k = ids();
            var mid = {
              x: (pointers[k[0]].x + pointers[k[1]].x) / 2,
              y: (pointers[k[0]].y + pointers[k[1]].y) / 2,
            };
            zoomAround(mid.x, mid.y, ratio > 1 ? 1 : -1);
            pinchBase = spread();
            return;
          }
        }
        schedule();
      });

      var end = function (e) {
        if (!pointers[e.pointerId]) return;
        delete pointers[e.pointerId];
        pinchBase = ids().length === 2 ? spread() : 0;
        if (!ids().length) {
          dragging = false;
          el.classList.remove("pm-dragging");
          changed();
        }
      };
      el.addEventListener("pointerup", end);
      el.addEventListener("pointercancel", end);

      el.addEventListener("dblclick", function (e) {
        var p = local(e);
        zoomAround(p.x, p.y, 1);
      });

      var wheelAt = 0;
      el.addEventListener(
        "wheel",
        function (e) {
          e.preventDefault();
          var t = Date.now();
          if (t - wheelAt < 220) return;
          wheelAt = t;
          var p = local(e);
          zoomAround(p.x, p.y, e.deltaY < 0 ? 1 : -1);
        },
        { passive: false }
      );

      // صفحه‌کلید: فلش‌ها جابه‌جا، +/- بزرگ‌نمایی
      el.tabIndex = 0;
      el.addEventListener("keydown", function (e) {
        var step = 80;
        var moves = { ArrowUp: [0, -step], ArrowDown: [0, step], ArrowLeft: [-step, 0], ArrowRight: [step, 0] };
        if (moves[e.key]) {
          e.preventDefault();
          c.x += moves[e.key][0];
          c.y += moves[e.key][1];
          clampCenter();
          render();
          changed();
        } else if (e.key === "+" || e.key === "=") {
          zoomBy(1);
        } else if (e.key === "-") {
          zoomBy(-1);
        }
      });
    }

    if (window.ResizeObserver) new ResizeObserver(schedule).observe(el);
    render();

    return { setView: setView, zoomBy: zoomBy, getCenter: center, el: el };
  }

  // مختصات را از لینک نشان/بلد/گوگل‌مپ یا متنِ «عرض، طول» بیرون می‌کشد
  function parseLink(text) {
    var s = String(text || "")
      .replace(/[۰-۹]/g, function (d) { return "۰۱۲۳۴۵۶۷۸۹".indexOf(d); })
      .replace(/[٠-٩]/g, function (d) { return "٠١٢٣٤٥٦٧٨٩".indexOf(d); })
      .replace(/%2C/gi, ",")
      .replace(/٫/g, ".")
      .trim();
    var num = "(-?\\d{1,3}(?:\\.\\d+)?)";
    var patterns = [
      new RegExp("!3d" + num + "!4d" + num),
      new RegExp("[?&](?:q|query|ll|destination|daddr|center)=(?:loc:)?" + num + ",\\s*" + num),
      new RegExp("latitude=" + num + ".*?longitude=" + num),
      new RegExp("[?&]lat=" + num + ".*?[?&](?:lng|lon|long)=" + num),
      new RegExp("@" + num + ",\\s*" + num),
      new RegExp("geo:" + num + ",\\s*" + num),
      new RegExp("^" + num + "\\s*[,،\\s]\\s*" + num + "$"),
    ];
    for (var i = 0; i < patterns.length; i++) {
      var m = s.match(patterns[i]);
      if (m) {
        var lat = parseFloat(m[1]);
        var lng = parseFloat(m[2]);
        if (Math.abs(lat) <= 85 && Math.abs(lng) <= 180 && (lat || lng)) {
          return { lat: lat, lng: lng };
        }
      }
    }
    return null;
  }

  // نقشه‌های ثابتِ نمایشی — فقط وقتی به صفحه رسیدند کاشی بار می‌شود
  function autoInit() {
    var els = document.querySelectorAll("[data-pin-map]:not([data-pm-ready])");
    var boot = function (el) {
      el.setAttribute("data-pm-ready", "");
      create(el, {
        lat: el.dataset.lat,
        lng: el.dataset.lng,
        zoom: +el.dataset.zoom || 16,
        interactive: false,
      });
    };
    if (!("IntersectionObserver" in window)) {
      els.forEach(boot);
      return;
    }
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) {
            io.unobserve(en.target);
            boot(en.target);
          }
        });
      },
      { rootMargin: "200px" }
    );
    els.forEach(function (el) { io.observe(el); });
  }

  window.PinMap = { create: create, parseLink: parseLink, autoInit: autoInit };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", autoInit);
  } else {
    autoInit();
  }
})();
