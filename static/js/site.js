(function () {
  'use strict';

  var SCROLL_TOP_THRESHOLD = 400;

  var header = document.getElementById('site-header');
  var meter = document.querySelector('.readmeter');
  var fill = document.querySelector('.readmeter__fill');
  var lastY = 0;
  var scrollRaf = false;

  var btnScrollTop = document.getElementById('btn-scroll-top');
  var btnShare = document.getElementById('btn-share-url');
  var toastEl = document.getElementById('site-toast');

  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  var tocHeadings = null;
  var tocLinks = null;

  function showToast(message) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.classList.add('is-visible');
    window.clearTimeout(showToast._t);
    showToast._t = window.setTimeout(function () {
      toastEl.classList.remove('is-visible');
    }, 2600);
  }

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      showToast('Copied to clipboard');
    } catch (e) {
      showToast('Could not copy');
    }
    document.body.removeChild(ta);
  }

  function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(function () {
        showToast('Copied to clipboard');
      }).catch(function () {
        fallbackCopy(text);
      });
    }
    fallbackCopy(text);
    return Promise.resolve();
  }

  function initShareButton() {
    if (!btnShare) return;
    var path = window.location.pathname || '/';
    if (path === '/' || path === '') {
      btnShare.hidden = true;
      return;
    }
    btnShare.hidden = false;
    btnShare.addEventListener('click', function () {
      copyToClipboard(window.location.href);
    });
  }

  function initScrollTop() {
    if (!btnScrollTop) return;
    btnScrollTop.addEventListener('click', function () {
      window.scrollTo({
        top: 0,
        behavior: prefersReducedMotion ? 'auto' : 'smooth'
      });
    });
  }

  function updateScrollTopVisibility(y) {
    if (!btnScrollTop) return;
    btnScrollTop.hidden = y < SCROLL_TOP_THRESHOLD;
  }

  function updateTocActive(y) {
    if (!tocHeadings || !tocLinks || tocHeadings.length === 0) return;
    var scrollPos = y + 120;
    var current = '';
    tocHeadings.forEach(function (h) {
      if (h.offsetTop <= scrollPos) current = h.id;
    });
    tocLinks.forEach(function (a) {
      a.classList.toggle('is-active', current && a.getAttribute('href') === '#' + current);
    });
  }

  function update() {
    scrollRaf = false;
    var y = window.scrollY || document.documentElement.scrollTop;

    if (fill) {
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var p = max > 0 ? (y / max) * 100 : 0;
      var n = Math.min(100, Math.max(0, Math.round(p)));
      fill.style.width = n + '%';
      fill.setAttribute('aria-valuenow', String(n));
    }

    updateScrollTopVisibility(y);
    updateTocActive(y);

    if (header) {
      if (y < 8) {
        header.classList.remove('global-nav--hidden');
      } else if (y > lastY && y > 56) {
        header.classList.add('global-nav--hidden');
      } else if (y < lastY) {
        header.classList.remove('global-nav--hidden');
      }
      lastY = y;
    }
  }

  function onScroll() {
    if (!scrollRaf) {
      scrollRaf = true;
      requestAnimationFrame(update);
    }
  }

  function slugify(text) {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')
      .slice(0, 48) || 'section';
  }

  function initToc() {
    var rail = document.getElementById('piece-rail');
    var nav = document.getElementById('piece-rail-nav');
    var prose = document.querySelector('.piece .prose');
    if (!rail || !nav || !prose) return;

    var headings = prose.querySelectorAll('h2');
    if (headings.length === 0) return;

    var used = {};
    headings.forEach(function (h, i) {
      var id = h.id;
      if (!id) {
        var base = slugify(h.textContent || 'section-' + (i + 1));
        id = base;
        var n = 2;
        while (used[id] || document.getElementById(id)) {
          id = base + '-' + n;
          n++;
        }
        used[id] = true;
        h.id = id;
      }
      var a = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = (h.textContent || 'Section').trim().slice(0, 80);
      nav.appendChild(a);
    });

    rail.hidden = false;
    tocHeadings = headings;
    tocLinks = nav.querySelectorAll('a');
  }

  initShareButton();
  initScrollTop();
  initToc();

  window.addEventListener('scroll', onScroll, { passive: true });
  update();
})();
