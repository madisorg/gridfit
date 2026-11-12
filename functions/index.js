// Cloudflare Pages Function for "/": the front door opens on the visitor's own country grid view. The country
// is the user's own choice when there is one (the gf-cc cookie the home page's country links set), else
// CF-IPCountry when it is one of the countries the site covers (data/countries.yaml `scope: in`; web/test/scope.mjs
// keeps this set equal to it). A choice the site no longer covers, crawlers, a request with a query string (/?all)
// and visitors from elsewhere get the neutral home page. Nothing is stored or logged.
const CC = new Set(["AT", "BE", "CZ", "DE", "EE", "ES", "IT", "NL", "PL", "SE"]);

export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.search) return next();
  const ua = request.headers.get("user-agent") || "";
  if (/bot|crawl|spider|slurp|lighthouse|preview/i.test(ua)) return next();
  const m = /(?:^|;\s*)gf-cc=([A-Za-z]{2})/.exec(request.headers.get("cookie") || "");
  if (m && !CC.has(m[1].toUpperCase())) return next();
  const cc = (m ? m[1] : request.headers.get("cf-ipcountry") || "").toUpperCase();
  if (!CC.has(cc)) return next();
  return new Response(null, { status: 302, headers: { location: `/grid/${cc.toLowerCase()}/`, "cache-control": "no-store", vary: "cookie" } });
}
