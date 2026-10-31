// Cloudflare Pages Function for "/": the front door opens on the visitor's own country grid view. The country
// is the user's own choice when there is one (the gf-cc cookie the home page's country select sets), else
// CF-IPCountry when it is one of the EU+ countries the site describes. Crawlers, a request with a query string
// (/?all) and visitors from elsewhere get the neutral home page. Nothing is stored or logged.
const CC = new Set(["AL", "AT", "BA", "BE", "BG", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GB", "GE", "GR", "HR", "HU", "IE", "IS", "IT", "LI", "LT", "LU", "LV", "MD", "ME", "MK", "MT", "NI", "NL", "NO", "PL", "PT", "RO", "RS", "SE", "SI", "SK", "TR", "UA", "XK"]);

export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.search) return next();
  const ua = request.headers.get("user-agent") || "";
  if (/bot|crawl|spider|slurp|lighthouse|preview/i.test(ua)) return next();
  const m = /(?:^|;\s*)gf-cc=([A-Za-z]{2})/.exec(request.headers.get("cookie") || "");
  let cc = m ? m[1].toUpperCase() : "";
  if (!CC.has(cc)) cc = (request.headers.get("cf-ipcountry") || "").toUpperCase();
  if (!CC.has(cc)) return next();
  return new Response(null, { status: 302, headers: { location: `/grid/${cc.toLowerCase()}/`, "cache-control": "no-store", vary: "cookie" } });
}
