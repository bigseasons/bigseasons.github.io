/* 개인정보처리방침·이용약관 공용 렌더러.
   본문은 legal/{privacy,terms}.json (tools/build_legal.py 가 앱 저장소 원본에서 만든다).
   언어 고르기는 index.html 과 같은 규칙: 메뉴에서 직접 고른 값('site-lang')만 기억, 그 밖엔 브라우저 언어. */
(function () {
  'use strict';

  var DOC = document.documentElement.getAttribute('data-doc');   // 'privacy' | 'terms'
  var LANG_KEY = 'site-lang';
  var LANGS = {
    ko: { name: '한국어',   locale: 'ko-KR' },
    en: { name: 'English',  locale: 'en-US' },
    ja: { name: '日本語',   locale: 'ja-JP' },
    zh: { name: '繁體中文', locale: 'zh-TW' }
  };
  var UI = {
    ko: { back: '홈으로', toc: '목차', privacy: '개인정보처리방침', terms: '이용약관', maker: '· 까먹지마를 만듭니다', brand: '까먹지마', notice: '' },
    en: { back: 'Back to home', toc: 'Contents', privacy: 'Privacy Policy', terms: 'Terms of Service', maker: '· makers of Amatdda', brand: 'Amatdda',
          notice: 'This page is a translation. If there is any difference in meaning, the Korean original prevails.' },
    ja: { back: 'ホームへ', toc: '目次', privacy: '個人情報保護方針', terms: '利用規約', maker: '· Amatdda をつくっています', brand: 'Amatdda',
          notice: 'このページは翻訳です。内容に相違がある場合は、韓国語の原文が優先します。' },
    zh: { back: '回首頁', toc: '目錄', privacy: '隱私政策', terms: '服務條款', maker: '· Amatdda 的開發者', brand: 'Amatdda',
          notice: '本頁為翻譯版本。內容如有出入，以韓文原文為準。' }
  };
  var data = null;

  function $(id) { return document.getElementById(id); }

  function render(code) {
    var d = data[code] || data.ko, ui = UI[code];
    document.documentElement.lang = LANGS[code].locale;
    document.title = d.title + ' | ' + ui.brand;
    $('brand').textContent = ui.brand;
    $('back').textContent = ui.back;
    $('title').textContent = d.title;
    $('meta').innerHTML = d.meta;            // 생성기가 이스케이프한 HTML
    $('notice').textContent = ui.notice;
    $('notice').hidden = !ui.notice;
    $('f-maker').textContent = ui.maker;
    $('f-privacy').textContent = ui.privacy;
    $('f-terms').textContent = ui.terms;

    var toc = $('toc'), body = $('body');
    toc.textContent = ''; body.textContent = '';
    toc.setAttribute('aria-label', ui.toc);
    var titled = d.sections.filter(function (s) { return s.h; }).length;
    toc.hidden = titled < 4;                  // 짧은 약관에는 목차를 두지 않는다
    d.sections.forEach(function (s, i) {
      var sec = document.createElement('section');
      sec.id = 's' + (i + 1);
      if (s.h) {
        var h = document.createElement('h2'); h.innerHTML = s.h; sec.appendChild(h);
        var li = document.createElement('li'), a = document.createElement('a');
        a.href = '#' + sec.id; a.innerHTML = s.h; li.appendChild(a); toc.appendChild(li);
      }
      sec.insertAdjacentHTML('beforeend', s.html);
      body.appendChild(sec);
    });

    $('lang-btn').textContent = LANGS[code].name;
    document.querySelectorAll('#lang-menu button').forEach(function (b) {
      b.setAttribute('aria-current', String(b.getAttribute('data-lang') === code));
    });
    if (location.hash) { var target = document.getElementById(location.hash.slice(1)); if (target) { target.scrollIntoView(); } }
  }

  var btn = $('lang-btn'), menu = $('lang-menu');
  function closeMenu() { menu.classList.remove('open'); btn.setAttribute('aria-expanded', 'false'); }
  btn.addEventListener('click', function (e) {
    e.stopPropagation();
    btn.setAttribute('aria-expanded', String(menu.classList.toggle('open')));
  });
  menu.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-lang]');
    if (!b || !data) { return; }
    var code = b.getAttribute('data-lang');
    render(code);
    try { localStorage.setItem(LANG_KEY, code); } catch (err) { /* 저장 불가 시 무시 */ }
    closeMenu();
  });
  document.addEventListener('click', closeMenu);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') { closeMenu(); } });

  var saved = null;
  try { saved = localStorage.getItem(LANG_KEY); } catch (e) { /* 접근 불가 시 무시 */ }
  var nav = (navigator.language || 'ko').toLowerCase();
  var detected = nav.indexOf('ko') === 0 ? 'ko' : nav.indexOf('ja') === 0 ? 'ja' : nav.indexOf('zh') === 0 ? 'zh' : 'en';
  var start = LANGS[saved] ? saved : detected;

  fetch('legal/' + DOC + '.json').then(function (r) {
    if (!r.ok) { throw new Error(DOC + ' ' + r.status); }
    return r.json();
  }).then(function (j) { data = j; render(start); }).catch(function () {
    $('loading').hidden = false;
  });
})();
