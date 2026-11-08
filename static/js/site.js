/**
 * TushN101 — Fast, Snappy Personal Tech Blog
 */
(function () {
  'use strict';

  var SCROLL_TOP_THRESHOLD = 300;
  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // DOM Elements
  var menuToggle = document.getElementById('menuToggle');
  var scrim = document.getElementById('scrim');
  var feed = document.getElementById('feed');
  var feedTabs = document.getElementById('feedTabs');
  var emptyMsg = document.getElementById('emptyMsg');
  var readmeterFill = document.getElementById('readmeter-fill');
  var btnScrollTop = document.getElementById('btn-scroll-top');
  var btnShareUrl = document.getElementById('btn-share-url');
  var topbarShareBtn = document.getElementById('topbarShareBtn');
  var toastEl = document.getElementById('site-toast');

  var scrollRaf = false;

  /* ============================================================
     1. Toast Notifications
     ============================================================ */
  var toastTimer = null;
  function showToast(message) {
    if (!toastEl) return;
    toastEl.textContent = message;
    toastEl.classList.add('is-visible');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toastEl.classList.remove('is-visible');
    }, 2200);
  }

  /* ============================================================
     2. Clipboard Helpers
     ============================================================ */
  function copyText(text, successMsg) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        showToast(successMsg || 'Copied to clipboard');
      }).catch(function () {
        fallbackCopy(text, successMsg);
      });
    } else {
      fallbackCopy(text, successMsg);
    }
  }

  function fallbackCopy(text, successMsg) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.setAttribute('readonly', '');
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
      showToast(successMsg || 'Copied to clipboard');
    } catch (e) {
      showToast('Could not copy');
    }
    document.body.removeChild(ta);
  }

  /* ============================================================
     3. Instant Link Hover Prefetching (< 15ms Click-to-Render)
     ============================================================ */
  var prefetchedUrls = new Set();
  function prefetchUrl(url) {
    if (!url || prefetchedUrls.has(url)) return;
    if (url.startsWith('#') || url.startsWith('mailto:') || url.startsWith('javascript:')) return;
    if (url.startsWith('http') && !url.startsWith(window.location.origin)) return;

    prefetchedUrls.add(url);
    var link = document.createElement('link');
    link.rel = 'prefetch';
    link.href = url;
    link.as = 'document';
    document.head.appendChild(link);
  }

  function initHoverPrefetch() {
    document.addEventListener('mouseover', function (e) {
      var a = e.target.closest('a');
      if (a && a.href) {
        var href = a.getAttribute('href');
        if (href && (href.startsWith('/') || href.startsWith(window.location.origin))) {
          prefetchUrl(a.href);
        }
      }
    }, { passive: true });
  }

  /* ============================================================
     4. Hamburger Sidebar Toggle (Desktop & Mobile)
     ============================================================ */
  function initSidebarToggle() {
    // Restore desktop preference on load
    if (window.innerWidth > 960) {
      try {
        if (localStorage.getItem('sidebar_collapsed') === '1') {
          document.body.classList.add('sidebar-collapsed');
        }
      } catch (e) {}
    }

    if (menuToggle) {
      menuToggle.addEventListener('click', function () {
        if (window.innerWidth > 960) {
          document.body.classList.toggle('sidebar-collapsed');
          var isCollapsed = document.body.classList.contains('sidebar-collapsed');
          try {
            localStorage.setItem('sidebar_collapsed', isCollapsed ? '1' : '0');
          } catch (e) {}
        } else {
          document.body.classList.toggle('menu-open');
        }
      });
    }

    if (scrim) {
      scrim.addEventListener('click', function () {
        document.body.classList.remove('menu-open');
      });
    }

    window.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        if (document.body.classList.contains('menu-open')) {
          document.body.classList.remove('menu-open');
        }
      }
    });
  }

  /* ============================================================
     5. Scraper-Protected Email Reveal Button
     ============================================================ */
  function initEmailReveal() {
    var btn = document.getElementById('btnRevealEmail');
    var container = document.getElementById('emailRevealContainer');
    if (!btn || !container) return;

    btn.addEventListener('click', function () {
      // Assemble at runtime to prevent automated crawlers
      var user = ['t', 'u', 's', 'h', 'n', '4', 'u'].join('');
      var domain = ['g', 'm', 'a', 'i', 'l', '.', 'c', 'o', 'm'].join('');
      var email = user + '@' + domain;

      container.innerHTML =
        '<div class="revealed-email-row">' +
          '<a href="mailto:' + email + '" class="revealed-email-link">' +
            '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>' +
            '<span>' + email + '</span>' +
          '</a>' +
          '<button type="button" class="pill-btn-sm" id="btnCopyEmail" title="Copy email address">' +
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>' +
            '<span>Copy</span>' +
          '</button>' +
        '</div>';

      var copyBtn = document.getElementById('btnCopyEmail');
      if (copyBtn) {
        copyBtn.addEventListener('click', function () {
          copyText(email, 'Email copied to clipboard');
        });
      }

      showToast('Email revealed');
    });
  }

  /* ============================================================
     6. Feed Tab and Topic Filtering
     ============================================================ */
  var currentTab = 'all';

  function filterFeed() {
    if (!feed) return;
    var posts = feed.querySelectorAll('.post');
    if (!posts || posts.length === 0) return;

    var visibleCount = 0;

    posts.forEach(function (post) {
      var cat = post.getAttribute('data-category') || '';
      var isFeatured = post.getAttribute('data-featured') === 'true';

      var match = true;
      if (currentTab === 'featured') {
        match = isFeatured;
      } else if (currentTab === 'deepdives') {
        match = cat === 'api' || cat === 'network' || cat === 'crypto';
      } else if (currentTab !== 'all') {
        match = cat === currentTab;
      }

      if (match) {
        post.classList.remove('is-hidden');
        visibleCount++;
      } else {
        post.classList.add('is-hidden');
      }
    });

    if (emptyMsg) {
      emptyMsg.hidden = visibleCount > 0;
    }
  }

  function initFeedFilters() {
    if (feedTabs) {
      var tabs = feedTabs.querySelectorAll('.tab');
      tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
          tabs.forEach(function (t) {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
          });
          tab.classList.add('active');
          tab.setAttribute('aria-selected', 'true');
          currentTab = tab.getAttribute('data-tab') || 'all';
          filterFeed();
        });
      });
    }

    var topicButtons = document.querySelectorAll('[data-topic-filter]');
    topicButtons.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var topic = btn.getAttribute('data-topic-filter');
        if (feed) {
          if (feedTabs) {
            feedTabs.querySelectorAll('.tab').forEach(function (t) { t.classList.remove('active'); });
          }
          currentTab = topic === 'all' ? 'all' : topic;
          filterFeed();
          feed.scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'start' });
        } else {
          window.location.href = '/?topic=' + topic;
        }

        if (document.body.classList.contains('menu-open')) {
          document.body.classList.remove('menu-open');
        }
      });
    });

    document.addEventListener('click', function (e) {
      var copyBtn = e.target.closest('.btn-copy-post');
      if (copyBtn) {
        e.preventDefault();
        e.stopPropagation();
        var relUrl = copyBtn.getAttribute('data-url');
        var fullUrl = window.location.origin + relUrl;
        copyText(fullUrl, 'Link copied to clipboard');
      }
    });
  }

  /* ============================================================
     7. Scroll Progress Meter & Floating Dock
     ============================================================ */
  function updateScroll() {
    scrollRaf = false;
    var y = window.scrollY || document.documentElement.scrollTop;

    if (readmeterFill) {
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var pct = max > 0 ? (y / max) * 100 : 0;
      var clamped = Math.min(100, Math.max(0, Math.round(pct)));
      readmeterFill.style.width = clamped + '%';
      readmeterFill.setAttribute('aria-valuenow', String(clamped));
    }

    if (btnScrollTop) {
      btnScrollTop.hidden = y < SCROLL_TOP_THRESHOLD;
    }
  }

  function onScroll() {
    if (!scrollRaf) {
      scrollRaf = true;
      requestAnimationFrame(updateScroll);
    }
  }

  function initScroll() {
    window.addEventListener('scroll', onScroll, { passive: true });
    updateScroll();

    if (btnScrollTop) {
      btnScrollTop.addEventListener('click', function () {
        window.scrollTo({
          top: 0,
          behavior: prefersReducedMotion ? 'auto' : 'smooth'
        });
      });
    }

    if (btnShareUrl) {
      btnShareUrl.addEventListener('click', function () {
        copyText(window.location.href, 'Page link copied to clipboard');
      });
    }

    if (topbarShareBtn) {
      topbarShareBtn.addEventListener('click', function () {
        copyText(window.location.href, 'Page link copied to clipboard');
      });
    }
  }

  function initUrlParams() {
    var params = new URLSearchParams(window.location.search);
    var topic = params.get('topic');
    if (topic && feed) {
      currentTab = topic;
      if (feedTabs) {
        var activeTab = feedTabs.querySelector('[data-tab="' + topic + '"]');
        if (activeTab) {
          feedTabs.querySelectorAll('.tab').forEach(function (t) { t.classList.remove('active'); });
          activeTab.classList.add('active');
        }
      }
      filterFeed();
    }
  }

  // Initialize
  initHoverPrefetch();
  initSidebarToggle();
  initEmailReveal();
  initFeedFilters();
  initScroll();
  initUrlParams();
})();
