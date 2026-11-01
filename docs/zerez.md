# ZEREZ — what is public, what the API gives, how to get access (2026-11-01)

ZEREZ (Zentrales Register für Einheiten- und Komponentenzertifikate) is run by FGW e.V., entrusted by the
federal economics ministry under § 49d(3) EnWG (terms of use, preamble). Since 1 February 2025 makers must
register their unit and component certificates there, and grid operators may take certificate data only
from the register (NELEV § 4(3), § 4(9)-(10), § 7(4)).

What was read for this file (no account, no login, nothing submitted): the web app's HTML and its client
bundle `https://www.zerez.net/static/js/main.72a3b793.js` (Last-Modified 2026-10-21, the same bundle
name the 2026-10 pass saw), the CMS pages the app loads (`shop.wind-fgw.de/wp-json/wp/v2/pages?slug=…`:
terms of use, FAQ, other documents), the user manual Rev. 5 (13.03.2026), the "Liste der
Netzanschlusswerte" for 4105 (Revision 1, EN), and the API's OpenAPI document
(`app-zerez-weeu-gatewaysvc-prod-01.azurewebsites.net/swagger/v1/swagger.json`).
**Not done:** a live anonymous query of the public unit list (the web app's GraphQL endpoint was not queried).
So whether the public list answers without login is still only what FAQ and manual say — a manual check in an
ordinary browser remains the proof.

## (a) The public view, without login

- FAQ (2025-12-10): "Der Zugriff auf die Registernummern (ZEREZ-ID) ist auch ohne Anmeldung möglich." and,
  for planners/installers/operators: "Eine Anmeldung ist nicht erforderlich, um das Register einzusehen.
  Erweiterte Funktionen sind nur nach erfolgreicher Registrierung verfügbar."
- What is public for **VDE-AR-N 4105** certificates (FAQ and manual Rev. 5 § 4.3, same words): the cover
  sheet of the proof document (annex E.4/E.5), the NA-protection certificate or test report (E.6/E.7), and
  the "Liste der Netzanschlusswerte" (the unit's grid-connection values). For 4110/4120/4130: the cover sheet
  (1.16) and attributes 1.01–1.16, 1.18, 1.20, 1.21, 1.25, 1.28, 1.68. Makers may widen visibility per user
  group or organisation; network operators always see the full value list.
- What the public unit overview carries (fields of the app's `getUnitsForUnitsOverview` query, run with
  `isLoggedIn = false` for anonymous visitors): model name, ZEREZ unit code, maker, certificate holder,
  certification body, certificate number and type, issue date, validity start/end, validity status,
  "replaced by" certificate, `is4105`, norm and its issue date, category, primary energy source, rated
  current and voltage, max active power (or power range), verification flag, open error reports. **No
  firmware field** in the overview; the 4105 value list has none either (fields 1.01–1.67); firmware is in
  the certificate PDF. The API has a `software_environment_version_number` field on certificates (below).
- ZEREZ-ID structure (FAQ): `ZE-R018-RV36-0001` = prefix, certification body, certificate, running unit
  number. A ZEREZ-ID may also stand for a maker's declaration or a prototype — the field "Art des
  Nachweisdokuments" (1.12) says which.
- Categories (API enum): Inverter, Storage Inverter, Asynchronous/Synchronous Generator, Fuel Cell,
  NA protection, PAV,E monitoring, Voltage Regulator, Intermediate Protective Device, EZA Controller,
  Other. **No wallbox / charger category** (bidirectional chargers would sit under storage — not seen).
- Validity statuses in the API: Verified / Verification Pending / Ongoing Feedback Process; FAQ: an
  "ungültig" certificate must not be used and its units must be disconnected. For 4105 certificates the
  rule sets only an issue date, so the maker marks an older certificate "Abgelaufen" when a new one exists
  (manual § 4.6).
- Reuse: the terms of use (2025-02-06) define "Empfänger von ZEREZ-Registerauskünften" and users "auch
  ohne Registrierung", but say nothing about copying or republishing register data; the CMS footer says
  "Alle Rechte vorbehalten". **No licence for reuse was found** — GridFit needs FGW's permission before it
  republishes ZEREZ rows (as planned for the permission letter).

## (b) The API for registered users

- **Who:** the OpenAPI text says "Server-To-Server API for all ZEREZ user"; the client bundle offers the
  "API-Schlüssel" tab under user management to every logged-in tenant (route scope "Home", not role-gated);
  pv magazine's FGW release says "allen registrierten Nutzerinnen und Nutzern". The older FAQ (2025-12-10)
  still says "Aktuell ist diese nur für Netzbetreiber verfügbar." → treat as: open to all registered
  organisations since the 2026 release (date not confirmed), what a key sees = what that organisation may
  see (public data plus anything a maker released to it; network operators see more).
- **Who may register:** "Hersteller von Erzeugungsanlagen, Netzbetreiber, Zertifizierungsstellen sowie
  Planer, Errichter und Betreiber von Energieerzeugungsanlagen" (FAQ; terms § 3.3). A legal person states
  the representative's name, the organisation's phone, name, **sector (Hersteller, Zertifizierungsstelle,
  Netzbetreiber oder Planer)** and seat; FGW checks plausibility and may ask for ID documents or proof of
  authority (commercial-register extract, power of attorney; foreign companies "vergleichbare Dokumente").
  Users must be adults with full legal capacity. A data/directory publisher is not a listed group — the
  nearest is "Planer" (project developer); say so honestly in the registration or ask FGW first.
- **Cost:** none. "ZEREZ ist ... kostenlos. Es entstehen keine Gebühren für die Registrierung und Nutzung
  der grundlegenden Funktionen des Registers." (FAQ)
- **Keys:** at most two API keys per organisation, created by the organisation's admin under
  Benutzerverwaltung → API-Schlüssel; the secret is shown once.
- **Auth:** OAuth2 client-credentials at `windfgwpublic.b2clogin.com` (tenant `windfgwpublic.onmicrosoft.com`,
  policy `b2c_1a_signinprd`), scope `https://windfgwpublic.onmicrosoft.com/1a33ef9b-b63c-45b1-90c1-669bf5516bf2/.default`;
  then `Authorization: Bearer <token>` against `https://app-zerez-weeu-gatewaysvc-prod-01.azurewebsites.net`.
  A 403 means the scope is missing — "Please create a ticket, if you want to request the scope for your client".
- **Limit:** 250 requests per hour (fixed window), 429 with `Retry-After` above it.
- **Endpoints (v1):** `POST /api/v1/units` (filters: manufacturers, certificateNumbers, maxActivePowerFrom/To,
  pageNumber, pageSize) → paged units with ~70 fields (model, ZEREZ code, P/S max and rated, voltage,
  current, short-circuit currents, phases, flicker and switching values, power ranges, inertia matrix,
  replaced_by, date_of_latest_change); `GET /api/v1/units/{zerezId}` (with its certificate);
  `POST /api/v1/certificates` (filters: manufacturers, certificateNumbers, certificateAuthorities, issued
  from/to) → certificate number, ZEREZ-ID, type, holder, certification body, norms, validity status, issue
  date, validity start/end, restrictions, **software_environment_version_number**, category, primary
  energy source, certificate files, date_of_latest_change; `GET /api/v1/certificates/{zerezId}` (with units).
- A full pull of the register at 250 requests/hour is feasible with large pages (page size limit not
  documented) — test after access.

## Access

API access needs a registered organisation account; creating it, and asking FGW for reuse permission before any ZEREZ row is
published on gridfit.eu, is the site owner's step. Until then GridFit shows makers' VDE-AR-N 4105 certificates as evidence
(data/evidence/) and no ZEREZ data.
