// Only collect traffic from the public site, never local development or previews.
if (location.hostname === 'iconwiki.aoo.kr') {
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { window.dataLayer.push(arguments); };
  window.gtag('js', new Date());
  window.gtag('config', 'G-N423N7QVBM', {
    allow_google_signals: false,
    allow_ad_personalization_signals: false,
  });

  const tag = document.createElement('script');
  tag.async = true;
  tag.src = 'https://www.googletagmanager.com/gtag/js?id=G-N423N7QVBM';
  document.head.appendChild(tag);
}
