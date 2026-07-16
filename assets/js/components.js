/* ============================================================================
   THEONIX OS — shared chrome (nav + footer)
   Single source of truth for the header and footer, injected into every page.
   Eliminates duplicated markup. Nav is position:fixed and the footer is the
   last element, so injection causes no cumulative layout shift.
   ========================================================================== */
(function () {
  'use strict';

  // Primary navigation (data-driven so every page stays in sync)
  var NAV = [
    { href: 'features.html', label: 'Features' },
    { href: 'screenshots.html', label: 'Screenshots' },
    { href: 'download.html', label: 'Download' },
    { href: 'documentation.html', label: 'Docs' },
    { href: 'roadmap.html', label: 'Roadmap' },
    { href: 'community.html', label: 'Community' }
  ];

  var FOOTER = {
    Product: [
      ['features.html', 'Features'],
      ['screenshots.html', 'Screenshots'],
      ['download.html', 'Download'],
      ['roadmap.html', 'Roadmap'],
      ['changelog.html', 'Changelog'],
      ['release-notes.html', 'Release notes']
    ],
    Resources: [
      ['documentation.html', 'Documentation'],
      ['verify.html', 'Verify ISO'],
      ['faq.html', 'FAQ'],
      ['blog.html', 'Blog'],
      ['about.html', 'About'],
      ['brand.html', 'Brand guide']
    ],
    Community: [
      ['community.html', 'Get involved'],
      ['contributors.html', 'Contributors'],
      ['https://github.com/theonix-os/theonix', 'GitHub'],
      ['https://community.theonix.org/', 'Forum'],
      ['https://discord.gg/theonix', 'Discord']
    ]
  };

  var LOGO = 'assets/img/logo.svg';
  var GH = 'https://github.com/theonix-os/theonix';

  var here = (location.pathname.split('/').pop() || 'index.html').toLowerCase();
  if (here === '') here = 'index.html';

  function navLinks(mobile) {
    return NAV.map(function (i) {
      var active = i.href.toLowerCase() === here ? ' aria-current="page"' : '';
      var cls = mobile ? 'nav-link block py-3' : 'nav-link';
      return '<a class="' + cls + '" href="' + i.href + '"' + active + '>' + i.label + '</a>';
    }).join('');
  }

  var header =
    '<a href="#main" class="skip-link btn btn-primary btn-sm">Skip to content</a>' +
    '<header class="site-nav" data-nav>' +
      '<nav class="container-x nav-inner" aria-label="Primary">' +
        '<a href="index.html" class="brand" aria-label="Theonix OS home">' +
          '<img src="' + LOGO + '" alt="" width="34" height="34" loading="eager" decoding="async">' +
          '<span class="font-display text-lg">Theonix<span class="text-gradient-cyan">OS</span></span>' +
        '</a>' +
        '<div class="hidden lg:flex items-center gap-8">' + navLinks(false) + '</div>' +
        '<div class="hidden lg:flex items-center gap-3">' +
          '<a href="' + GH + '" class="btn btn-ghost btn-sm" rel="noopener" aria-label="Theonix on GitHub">' +
            '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2C6.48 2 2 6.58 2 12.26c0 4.5 2.87 8.32 6.84 9.67.5.09.68-.22.68-.48v-1.7c-2.78.62-3.37-1.2-3.37-1.2-.45-1.18-1.11-1.5-1.11-1.5-.91-.63.07-.62.07-.62 1 .07 1.53 1.05 1.53 1.05.9 1.57 2.36 1.12 2.94.85.09-.66.35-1.12.63-1.38-2.22-.26-4.56-1.14-4.56-5.06 0-1.12.39-2.03 1.03-2.75-.1-.26-.45-1.3.1-2.7 0 0 .84-.28 2.75 1.05a9.3 9.3 0 0 1 5 0c1.91-1.33 2.75-1.05 2.75-1.05.55 1.4.2 2.44.1 2.7.64.72 1.03 1.63 1.03 2.75 0 3.93-2.35 4.79-4.58 5.05.36.32.68.94.68 1.9v2.82c0 .27.18.58.69.48A10.02 10.02 0 0 0 22 12.26C22 6.58 17.52 2 12 2Z"/></svg>' +
            'GitHub</a>' +
          '<a href="download.html" class="btn btn-primary btn-sm">Get Theonix</a>' +
        '</div>' +
        '<button class="nav-toggle lg:hidden" data-nav-toggle aria-expanded="false" aria-controls="mobile-menu" aria-label="Open menu">' +
          '<svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" d="M4 7h16M4 12h16M4 17h16"/></svg>' +
        '</button>' +
      '</nav>' +
      '<div class="mobile-menu lg:hidden" id="mobile-menu" data-mobile-menu>' +
        '<div class="container-x py-4">' + navLinks(true) +
          '<a href="download.html" class="btn btn-primary btn-block mt-3">Download Theonix OS</a>' +
        '</div>' +
      '</div>' +
    '</header>';

  function footerCol(title) {
    var items = FOOTER[title].map(function (l) {
      var ext = l[0].indexOf('http') === 0 ? ' rel="noopener"' : '';
      return '<li><a class="text-muted hover:text-white transition" href="' + l[0] + '"' + ext + '>' + l[1] + '</a></li>';
    }).join('');
    return '<nav aria-label="' + title + '"><h2 class="font-semibold text-sm">' + title + '</h2>' +
      '<ul class="mt-4 space-y-2.5 text-[0.95rem]">' + items + '</ul></nav>';
  }

  var year = new Date().getFullYear();
  var footer =
    '<footer class="border-t border-white/5 pt-16 pb-10 mt-8">' +
      '<div class="container-x">' +
        '<div class="grid gap-10 md:grid-cols-2 lg:grid-cols-5">' +
          '<div class="lg:col-span-2">' +
            '<a href="index.html" class="brand"><img src="' + LOGO + '" alt="" width="32" height="32" loading="lazy" decoding="async">' +
              '<span class="font-display text-lg">Theonix<span class="text-gradient-cyan">OS</span></span></a>' +
            '<p class="text-muted mt-4 max-w-sm text-[0.95rem]">A modern Arch-based Linux distribution with KDE&nbsp;Plasma&nbsp;6, Wayland and a rolling release model. Free and open source.</p>' +
            '<p class="text-faint mt-4 font-mono text-sm">v1.0 &ldquo;Genesis&rdquo;</p>' +
          '</div>' +
          footerCol('Product') + footerCol('Resources') + footerCol('Community') +
        '</div>' +
        '<div class="divider mt-12"></div>' +
        '<div class="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">' +
          '<p class="text-sm text-muted">&copy; ' + year + ' Theonix OS &middot; Created by Kelvin Benny Koshy</p>' +
          '<p class="text-sm text-muted">Released under the GPL &middot; Built by the community</p>' +
        '</div>' +
      '</div>' +
    '</footer>';

  // Inject: header first in <body>, footer appended after <main>.
  var headerMount = document.querySelector('[data-site-header]');
  var footerMount = document.querySelector('[data-site-footer]');
  if (headerMount) headerMount.outerHTML = header; else document.body.insertAdjacentHTML('afterbegin', header);
  if (footerMount) footerMount.outerHTML = footer; else document.body.insertAdjacentHTML('beforeend', footer);
})();
