# Analytics

Production uses GA4 property **Icon Wiki** (`560109607`), web stream
**Icon Wiki Web** (`16178823126`), measurement ID `G-N423N7QVBM`.
`analytics.js` loads the Google tag only on `iconwiki.aoo.kr`, excluding local
development and preview hosts. Reporting uses Korea time and KRW.

GA4 collects page loads, visits, engagement time, scrolls, outbound link clicks,
and supported file downloads. Enhanced measurement's browser-history page views
are disabled because search/filter changes use `replaceState` and are not new
page visits. Automatic site search, form and video events are disabled. Google
signals and advertising personalization are disabled in the tag configuration.

Use Realtime for incoming traffic and the traffic/engagement reports for trends.
Closing a tab is not a guaranteed standalone exit event; use engagement and
bounce rate to understand short visits and departures.

[Open GA4](https://analytics.google.com/analytics/web/#/a401990895p560109607/reports/intelligenthome)
