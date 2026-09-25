/* CardNav — Vanilla JS port of the React Bits component (JS + CSS variant).
 * Mirrors the original behaviour:
 *  - collapsed height 60px; expanded 260px on desktop, measured on mobile
 *  - cards enter with y+opacity and 80ms stagger (GSAP power3.out easing is
 *    reproduced in CSS as cubic-bezier(0.215, 0.61, 0.355, 1), so no gsap dep)
 *  - timeline is rebuilt on resize while expanded, like the React version
 * Enhancements over the original: Escape/outside-click to close, synced ARIA.
 */
(function () {
  var COLLAPSED_HEIGHT = 60;
  var OPEN_DESKTOP_HEIGHT = 260;
  var STAGGER_MS = 80;

  var nav = document.querySelector('[data-card-nav]');
  if (!nav) return;

  var toggle = nav.querySelector('[data-card-nav-toggle]');
  var content = nav.querySelector('.card-nav-content');
  var cards = Array.prototype.slice.call(nav.querySelectorAll('.nav-card'));
  if (!toggle || !content) return;

  var isExpanded = false;

  function isMobile() {
    return window.matchMedia('(max-width: 768px)').matches;
  }

  /* Same measuring strategy as the React source: temporarily reveal the
   * content to read its natural height, then restore. */
  function calculateHeight() {
    if (!isMobile()) return OPEN_DESKTOP_HEIGHT;

    var prev = {
      visibility: content.style.visibility,
      pointerEvents: content.style.pointerEvents,
      position: content.style.position,
      height: content.style.height
    };

    content.style.visibility = 'visible';
    content.style.pointerEvents = 'auto';
    content.style.position = 'static';
    content.style.height = 'auto';

    // Force reflow so scrollHeight is up to date.
    void content.offsetHeight;

    var topBar = 60;
    var padding = 16;
    var contentHeight = content.scrollHeight;

    content.style.visibility = prev.visibility;
    content.style.pointerEvents = prev.pointerEvents;
    content.style.position = prev.position;
    content.style.height = prev.height;

    return topBar + contentHeight + padding;
  }

  function syncAria() {
    toggle.setAttribute('aria-expanded', isExpanded ? 'true' : 'false');
    toggle.setAttribute('aria-label', isExpanded ? 'بستن منو' : 'باز کردن منو');
    content.setAttribute('aria-hidden', isExpanded ? 'false' : 'true');
  }

  function open() {
    isExpanded = true;
    toggle.classList.add('open');
    nav.classList.add('open');
    nav.style.height = calculateHeight() + 'px';
    cards.forEach(function (card, i) {
      card.style.transitionDelay = i * STAGGER_MS + 'ms';
    });
    syncAria();
  }

  function close() {
    isExpanded = false;
    toggle.classList.remove('open');
    nav.classList.remove('open');
    nav.style.height = COLLAPSED_HEIGHT + 'px';
    cards.forEach(function (card) {
      card.style.transitionDelay = '0ms';
    });
    syncAria();
  }

  function toggleMenu() {
    if (isExpanded) close();
    else open();
  }

  toggle.addEventListener('click', toggleMenu);

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && isExpanded) close();
  });

  document.addEventListener('click', function (e) {
    if (isExpanded && !nav.contains(e.target)) close();
  });

  window.addEventListener('resize', function () {
    // Keep the open height correct across breakpoints, like the React effect.
    if (isExpanded) {
      nav.style.height = calculateHeight() + 'px';
    }
  });

  // Initial state (matches gsap.set in the original).
  nav.style.height = COLLAPSED_HEIGHT + 'px';
  syncAria();
})();
