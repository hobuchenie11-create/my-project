/**
 * analytics.js — сбор поведенческих метрик для сайта-визитки.
 *
 * Без внешних зависимостей и без cookies. События копятся в localStorage
 * (кольцевой буфер) и, если задан endpoint, батчами отправляются на сервер.
 * Просмотр собранных данных — analytics.html.
 *
 * Конфигурация (задать до подключения скрипта):
 *   window.ANALYTICS_CONFIG = {
 *     endpoint: 'https://example.com/collect', // null — только локальное хранение
 *     debug: true                              // логирование событий в консоль
 *   };
 *
 * Отключение сбора для себя (в консоли): analytics.optOut()
 */
(function () {
  'use strict';

  var CFG = Object.assign({
    endpoint: null,
    storageKey: 'bc_analytics_events',
    visitorKey: 'bc_analytics_visitor',
    optOutKey: 'bc_analytics_optout',
    sessionKey: 'bc_analytics_session',
    maxStoredEvents: 2000,
    sessionTimeoutMin: 30,
    batchSize: 25,
    flushIntervalMs: 15000,
    scrollMarks: [25, 50, 75, 90, 100],
    debug: false
  }, window.ANALYTICS_CONFIG || {});

  // ── Хранилище ────────────────────────────────────────────────
  function lsGet(key, fallback) {
    try { return JSON.parse(localStorage.getItem(key)) || fallback; }
    catch (e) { return fallback; }
  }
  function lsSet(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* квота */ }
  }

  if (localStorage.getItem(CFG.optOutKey) === '1') {
    window.analytics = {
      track: function () {}, getEvents: function () { return []; },
      optOut: function () {}, optIn: function () { localStorage.removeItem(CFG.optOutKey); location.reload(); }
    };
    return;
  }

  // ── Посетитель и сессия ──────────────────────────────────────
  function uid() {
    return Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10);
  }

  var visitor = lsGet(CFG.visitorKey, null);
  var isNewVisitor = !visitor;
  if (!visitor) {
    visitor = { id: uid(), firstSeen: Date.now(), visits: 0 };
  }

  var session = null;
  try { session = JSON.parse(sessionStorage.getItem(CFG.sessionKey)); } catch (e) {}
  var now = Date.now();
  var isNewSession = !session || (now - session.lastActive) > CFG.sessionTimeoutMin * 60000;
  if (isNewSession) {
    session = { id: uid(), startedAt: now };
    visitor.visits += 1;
  }
  session.lastActive = now;
  try { sessionStorage.setItem(CFG.sessionKey, JSON.stringify(session)); } catch (e) {}
  lsSet(CFG.visitorKey, visitor);

  // ── Контекст окружения ───────────────────────────────────────
  function utmParams() {
    var out = {};
    var qs = new URLSearchParams(location.search);
    ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(function (k) {
      if (qs.has(k)) out[k] = qs.get(k);
    });
    return out;
  }

  var context = {
    url: location.pathname + location.search,
    referrer: document.referrer || null,
    lang: navigator.language,
    ua: navigator.userAgent,
    tz: (Intl.DateTimeFormat().resolvedOptions() || {}).timeZone || null,
    screen: screen.width + 'x' + screen.height,
    viewport: innerWidth + 'x' + innerHeight,
    dpr: devicePixelRatio || 1,
    deviceType: innerWidth < 768 ? 'mobile' : (innerWidth < 1200 ? 'tablet' : 'desktop'),
    utm: utmParams()
  };

  // ── Запись и отправка событий ────────────────────────────────
  var sendQueue = [];

  function track(name, props) {
    var event = {
      id: uid(),
      name: name,
      ts: Date.now(),
      visitorId: visitor.id,
      sessionId: session.id,
      props: props || {}
    };
    var events = lsGet(CFG.storageKey, []);
    events.push(event);
    if (events.length > CFG.maxStoredEvents) {
      events = events.slice(events.length - CFG.maxStoredEvents);
    }
    lsSet(CFG.storageKey, events);

    if (CFG.endpoint) sendQueue.push(event);
    if (CFG.debug) console.log('[analytics]', name, event.props);

    session.lastActive = Date.now();
    try { sessionStorage.setItem(CFG.sessionKey, JSON.stringify(session)); } catch (e) {}
    return event;
  }

  function flush(useBeacon) {
    if (!CFG.endpoint || sendQueue.length === 0) return;
    var batch = sendQueue.splice(0, useBeacon ? sendQueue.length : CFG.batchSize);
    var body = JSON.stringify({ context: context, events: batch });
    if (useBeacon && navigator.sendBeacon) {
      if (!navigator.sendBeacon(CFG.endpoint, new Blob([body], { type: 'application/json' }))) {
        sendQueue = batch.concat(sendQueue);
      }
      return;
    }
    fetch(CFG.endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body,
      keepalive: true
    }).catch(function () { sendQueue = batch.concat(sendQueue); });
  }

  if (CFG.endpoint) setInterval(function () { flush(false); }, CFG.flushIntervalMs);

  // ── Базовые события ──────────────────────────────────────────
  if (isNewSession) {
    track('session_start', {
      newVisitor: isNewVisitor,
      visitNumber: visitor.visits,
      referrer: context.referrer,
      utm: context.utm,
      deviceType: context.deviceType,
      lang: context.lang,
      screen: context.screen
    });
  }
  track('pageview', { url: context.url, title: document.title, deviceType: context.deviceType });

  // ── Просмотры секций ─────────────────────────────────────────
  var seenSections = {};
  var sectionObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting && !seenSections[entry.target.id]) {
        seenSections[entry.target.id] = true;
        track('section_view', { section: entry.target.id });
      }
    });
  }, { threshold: 0.4 });
  document.querySelectorAll('section[id]').forEach(function (el) { sectionObserver.observe(el); });

  // ── Клики ────────────────────────────────────────────────────
  function clickLabel(link) {
    var strong = link.querySelector('strong');
    var text = (strong ? strong.textContent : link.textContent).trim().replace(/\s+/g, ' ');
    return text.slice(0, 80);
  }

  document.addEventListener('click', function (e) {
    var link = e.target.closest('a, button');
    if (!link) return;
    var href = link.getAttribute('href') || null;
    var kind = 'link';
    if (link.closest('.contact-item')) kind = 'contact';
    else if (link.closest('nav')) kind = 'nav';
    else if (link.classList.contains('btn')) kind = 'cta';
    track('click', { kind: kind, label: clickLabel(link), href: href });
  }, true);

  // ── Глубина прокрутки ────────────────────────────────────────
  var firedMarks = {};
  function onScroll() {
    var doc = document.documentElement;
    var max = doc.scrollHeight - innerHeight;
    var pct = max > 0 ? Math.round((scrollY / max) * 100) : 100;
    CFG.scrollMarks.forEach(function (mark) {
      if (pct >= mark && !firedMarks[mark]) {
        firedMarks[mark] = true;
        track('scroll_depth', { depth: mark });
      }
    });
  }
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ── Время вовлечённости (только видимая вкладка) ─────────────
  var engagedMs = 0;
  var visibleSince = document.visibilityState === 'visible' ? Date.now() : null;

  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') {
      visibleSince = Date.now();
    } else if (visibleSince) {
      engagedMs += Date.now() - visibleSince;
      visibleSince = null;
    }
  });

  var exitSent = false;
  function onExit() {
    if (exitSent) return;
    exitSent = true;
    if (visibleSince) {
      engagedMs += Date.now() - visibleSince;
      visibleSince = null;
    }
    track('engagement', {
      engagedSec: Math.round(engagedMs / 1000),
      maxScroll: Math.max.apply(null, [0].concat(Object.keys(firedMarks).map(Number))),
      sectionsSeen: Object.keys(seenSections)
    });
    flush(true);
  }
  addEventListener('pagehide', onExit);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') { onExit(); exitSent = false; }
  });

  // ── Ошибки JS ────────────────────────────────────────────────
  addEventListener('error', function (e) {
    track('error', {
      message: String(e.message).slice(0, 200),
      source: e.filename ? e.filename.split('/').pop() + ':' + e.lineno : null
    });
  });

  // ── Публичный API ────────────────────────────────────────────
  window.analytics = {
    track: track,
    getEvents: function () { return lsGet(CFG.storageKey, []); },
    clear: function () { localStorage.removeItem(CFG.storageKey); },
    optOut: function () { localStorage.setItem(CFG.optOutKey, '1'); },
    optIn: function () { localStorage.removeItem(CFG.optOutKey); },
    config: CFG
  };
})();
