// Cloudflare Pages Function: returns the visitor's country code from the CF-IPCountry header, so the home
// page can offer "open the Estonia view". Nothing is stored or logged; the browser keeps the user's own
// choice in localStorage. Crawlers get the neutral home page, never a redirect.
export function onRequest({ request }) {
  const cc = (request.headers.get("cf-ipcountry") || "").toUpperCase();
  return new Response(JSON.stringify({ cc: /^[A-Z]{2}$/.test(cc) ? cc : "" }), {
    headers: { "content-type": "application/json", "cache-control": "no-store", "access-control-allow-origin": "*" },
  });
}
