/* ============================================================================
   THEONIX OS — interactions
   Vanilla JS, no dependencies, progressive enhancement.
   Runs after components.js (both deferred, in order) so injected nav/footer
   elements are present.

   Modules: nav state · mobile menu · scroll reveal · card spotlight ·
   screenshots carousel · terminal typing · copy buttons · lightbox gallery ·
   download mirror selector.
   ========================================================================== */
(function () {
  'use strict';
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---- Navbar scroll state --------------------------------------------- */
  var nav = $('[data-nav]');
  if (nav) {
    var onScroll = function () { nav.classList.toggle('scrolled', window.scrollY > 20); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ---- Mobile menu ------------------------------------------------------ */
  var toggle = $('[data-nav-toggle]'), menu = $('[data-mobile-menu]');
  if (toggle && menu) {
    toggle.addEventListener('click', function () {
      var open = menu.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
    $$('a', menu).forEach(function (a) {
      a.addEventListener('click', function () {
        menu.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ---- Scroll reveal ---------------------------------------------------- */
  var reveals = $$('.reveal');
  if (reveals.length) {
    if (reduce || !('IntersectionObserver' in window)) {
      reveals.forEach(function (el) { el.classList.add('in'); });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            var d = e.target.getAttribute('data-delay') || 0;
            setTimeout(function () { e.target.classList.add('in'); }, d);
            io.unobserve(e.target);
          }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
      reveals.forEach(function (el) { io.observe(el); });
    }
  }

  /* ---- Card spotlight (cursor-follow glow) ------------------------------ */
  if (!reduce) {
    $$('.card-spot').forEach(function (card) {
      card.addEventListener('pointermove', function (e) {
        var r = card.getBoundingClientRect();
        card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
        card.style.setProperty('--my', (e.clientY - r.top) + 'px');
      });
    });
  }

  /* ---- Copy buttons ----------------------------------------------------- */
  $$('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-copy');
      var restore = btn.getAttribute('data-label') || btn.textContent;
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function () {
          btn.textContent = 'Copied ✓';
          setTimeout(function () { btn.textContent = restore; }, 1500);
        }).catch(function () {});
      }
    });
  });

  /* ---- Screenshots carousel -------------------------------------------- */
  $$('[data-carousel]').forEach(function (root) {
    var track = $('[data-carousel-track]', root);
    var slides = $$('.carousel-slide', root);
    var dotsWrap = $('[data-carousel-dots]', root);
    var prev = $('[data-carousel-prev]', root), next = $('[data-carousel-next]', root);
    if (!track || !slides.length) return;
    var index = 0, timer = null;

    var dots = slides.map(function (_, i) {
      var b = document.createElement('button');
      b.className = 'carousel-dot'; b.type = 'button';
      b.setAttribute('aria-label', 'Go to slide ' + (i + 1));
      b.addEventListener('click', function () { go(i, true); });
      if (dotsWrap) dotsWrap.appendChild(b);
      return b;
    });
    function render() {
      track.style.transform = 'translateX(' + (-index * 100) + '%)';
      dots.forEach(function (d, i) { d.classList.toggle('active', i === index); });
    }
    function go(i, user) { index = (i + slides.length) % slides.length; render(); if (user) restart(); }
    function auto() { if (!reduce) timer = setInterval(function () { go(index + 1); }, 5500); }
    function restart() { clearInterval(timer); auto(); }
    if (prev) prev.addEventListener('click', function () { go(index - 1, true); });
    if (next) next.addEventListener('click', function () { go(index + 1, true); });
    root.addEventListener('mouseenter', function () { clearInterval(timer); });
    root.addEventListener('mouseleave', auto);
    var sx = 0;
    root.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; }, { passive: true });
    root.addEventListener('touchend', function (e) {
      var dx = e.changedTouches[0].clientX - sx;
      if (Math.abs(dx) > 40) go(index + (dx < 0 ? 1 : -1), true);
    });
    render(); auto();
  });

  /* ---- Terminal typing animation ---------------------------------------- */
  var term = $('[data-terminal]');
  if (term) {
    var body = $('[data-terminal-body]', term);
    var script = [
      { t: 'cmd', text: 'fastfetch' },
      { t: 'out', text: 'theonix@genesis   OS: Theonix OS 1.0  ·  KDE Plasma 6 (Wayland)  ·  Kernel 6.x' },
      { t: 'cmd', text: 'sudo pacman -Syu' },
      { t: 'out', text: ':: Synchronising package databases…  core  extra  theonix  multilib' },
      { t: 'ok', text: '✓ System up to date — powered by the Theonix repository.' },
      { t: 'cmd', text: 'flatpak install flathub org.kde.kdenlive' },
      { t: 'ok', text: '✓ Installation complete.' }
    ];
    var started = false;
    function typeInto(target, text, done, speed) {
      speed = speed || 24;
      if (reduce) { target.insertAdjacentText('beforeend', text); return done(); }
      var i = 0;
      (function tick() {
        target.insertAdjacentText('beforeend', text[i]); body.scrollTop = body.scrollHeight; i++;
        if (i < text.length) setTimeout(tick, speed + Math.random() * 20); else setTimeout(done, 320);
      })();
    }
    function line(l, done) {
      var el = document.createElement('div'); el.className = 'term-line'; body.appendChild(el);
      if (l.t === 'cmd') {
        el.innerHTML = '<span class="term-prompt">theonix@genesis</span><span class="term-out">:</span><span class="term-path">~</span><span class="term-out">$ </span>';
        typeInto(el, l.text, done);
      } else {
        var cls = l.t === 'ok' ? 'term-ok' : (l.t === 'warn' ? 'term-warn' : 'term-out');
        var s = document.createElement('span'); s.className = cls; el.appendChild(s);
        typeInto(s, l.text, done, 6);
      }
    }
    function run(i) {
      if (i >= script.length) { var c = document.createElement('span'); c.className = 'term-cursor';
        body.appendChild(document.createElement('div')).appendChild(c); return; }
      line(script[i], function () { run(i + 1); });
    }
    function start() { if (started) return; started = true; body.innerHTML = ''; run(0); }
    if ('IntersectionObserver' in window) {
      var tio = new IntersectionObserver(function (es) {
        es.forEach(function (e) { if (e.isIntersecting) { start(); tio.disconnect(); } });
      }, { threshold: 0.35 });
      tio.observe(term);
    } else { start(); }
  }

  /* ---- Lightbox gallery ------------------------------------------------- */
  var triggers = $$('[data-lightbox]');
  if (triggers.length) {
    var lb = document.createElement('div');
    lb.className = 'lightbox'; lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true'); lb.setAttribute('aria-label', 'Screenshot preview');
    lb.innerHTML =
      '<button class="lightbox-close" aria-label="Close preview">' +
        '<svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" d="M6 6l12 12M18 6L6 18"/></svg></button>' +
      '<button class="lightbox-nav lightbox-prev" aria-label="Previous"><svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m15 18-6-6 6-6"/></svg></button>' +
      '<button class="lightbox-nav lightbox-next" aria-label="Next"><svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m9 18 6-6-6-6"/></svg></button>' +
      '<figure class="lightbox-figure"><div class="lightbox-stage" data-lb-stage></div><figcaption class="lightbox-cap" data-lb-cap></figcaption></figure>';
    document.body.appendChild(lb);
    var stage = $('[data-lb-stage]', lb), cap = $('[data-lb-cap]', lb);
    var current = 0, lastFocus = null;

    function html(i) {
      var t = triggers[i];
      var img = t.getAttribute('data-img');
      var label = t.getAttribute('data-caption') || t.getAttribute('aria-label') || '';
      if (img) return '<img src="' + img + '" alt="' + label + '" style="width:100%;display:block">';
      // fallback: clone the on-page preview surface
      var inner = t.querySelector('.shot') ? t.querySelector('.shot').outerHTML : t.innerHTML;
      return inner;
    }
    function show(i) {
      current = (i + triggers.length) % triggers.length;
      stage.innerHTML = html(current);
      cap.textContent = triggers[current].getAttribute('data-caption') || '';
    }
    function open(i) {
      lastFocus = document.activeElement;
      show(i); lb.classList.add('open');
      document.body.style.overflow = 'hidden';
      $('.lightbox-close', lb).focus();
    }
    function close() {
      lb.classList.remove('open'); document.body.style.overflow = '';
      if (lastFocus) lastFocus.focus();
    }
    triggers.forEach(function (t, i) {
      t.setAttribute('role', 'button'); t.setAttribute('tabindex', '0');
      t.addEventListener('click', function () { open(i); });
      t.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(i); }
      });
    });
    $('.lightbox-close', lb).addEventListener('click', close);
    $('.lightbox-prev', lb).addEventListener('click', function () { show(current - 1); });
    $('.lightbox-next', lb).addEventListener('click', function () { show(current + 1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft') show(current - 1);
      else if (e.key === 'ArrowRight') show(current + 1);
    });
  }

  /* ---- Download mirror selector ----------------------------------------
     The canonical download route (https://theonixos.xyz/download) hides the
     real storage provider. Selecting a mirror appends ?mirror=<id>; "Auto"
     omits it so the server can pick the fastest edge. If a mirror exposes a
     data-ping URL, a real latency probe re-labels the fastest option — until
     then it degrades gracefully with no invented numbers. ------------------ */
  var mirrorRoot = $('[data-mirrors]');
  if (mirrorRoot) {
    var base = mirrorRoot.getAttribute('data-base') || 'https://theonixos.xyz/download';
    var button = $('[data-download-btn]');
    var mirrors = $$('.mirror', mirrorRoot);

    function select(el) {
      mirrors.forEach(function (m) { m.setAttribute('aria-checked', 'false'); });
      el.setAttribute('aria-checked', 'true');
      var id = el.getAttribute('data-mirror-id');
      if (button) button.setAttribute('href', id && id !== 'auto' ? base + '?mirror=' + encodeURIComponent(id) : base);
    }
    mirrors.forEach(function (m) {
      m.setAttribute('role', 'radio');
      m.addEventListener('click', function () { select(m); });
      m.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); select(m); }
      });
    });

    // Optional real latency probe (only runs for mirrors with data-ping)
    if (!reduce) {
      mirrors.forEach(function (m) {
        var ping = m.getAttribute('data-ping');
        var out = $('[data-latency]', m);
        if (!ping || !out) return;
        var t0 = performance.now(); var done = false;
        var img = new Image();
        var finish = function (ok) {
          if (done) return; done = true;
          out.textContent = ok ? Math.round(performance.now() - t0) + ' ms' : '—';
        };
        img.onload = function () { finish(true); };
        img.onerror = function () { finish(false); };
        setTimeout(function () { finish(false); }, 4000);
        img.src = ping + (ping.indexOf('?') > -1 ? '&' : '?') + 't=' + Date.now();
      });
    }
  }
})();
