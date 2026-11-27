"use client";

import { useEffect, useRef, type CSSProperties } from "react";

export type FaqDrawerCard = {
  id: string;
  tab: string;
  q: string;
  a: string;
};

export type FaqDrawerOptions = {
  /** Small caps line above the title. */
  label?: string;
  title?: string;
  lead?: string;
  /** The text on the drawer's label holder. */
  drawer?: string;
  /** Custom FAQ cards. Defaults to built-in sample cards. */
  cards?: readonly FaqDrawerCard[];
  /** How many cards, 3 to 7. */
  count?: number;
  /** Which card starts open: "1" to "7", or "none". */
  open?: "none" | "1" | "2" | "3" | "4" | "5" | "6" | "7";
  /** Opening one card closes the others. */
  single?: boolean;
  askNote?: string;
  askLabel?: string;
  /** http(s), mailto, tel or a path. Anything else falls back to the default. */
  askHref?: string;
  /** "auto" follows the page: prefers-color-scheme, a .dark ancestor, or a [data-finish] ancestor. */
  finish?: "auto" | "aluminium" | "graphite";
};

/** Dark when a .dark / [data-theme=dark] ancestor says so, light when .light says so, else the system's setting. */
const isDark = (host: Element, mq: MediaQueryList | null): boolean => {
  if (host.closest(".dark, [data-theme='dark']")) return true;
  if (host.closest(".light, [data-theme='light']")) return false;
  return !!mq?.matches;
};

const CARDS: readonly FaqDrawerCard[] = Object.freeze([
  Object.freeze({
    id: 'billing', tab: 'Pricing',
    q: 'How is a run billed?',
    a: 'By the second an agent is awake: $0.000018 per GB-second, with the first 400,000 GB-seconds each month free. Sleeping between tool calls costs nothing, and a stopped run stops billing the second it stops.',
  }),
  Object.freeze({
    id: 'retention', tab: 'Data',
    q: 'How long do you keep run traces?',
    a: '30 days on Team, 365 on Scale, and as long as you like when you host Lode yourself. When the window closes a trace is deleted, not archived; until then you can export it as OpenTelemetry.',
  }),
  Object.freeze({
    id: 'sso', tab: 'SSO',
    q: 'Do you support SSO and SCIM?',
    a: 'Yes, on Scale: SAML 2.0 and OIDC with Okta, Entra ID, Google Workspace or any standard provider, and SCIM 2.0 for provisioning. Roles follow your groups, so leaving the company leaves Lode.',
  }),
  Object.freeze({
    id: 'uptime', tab: 'Uptime',
    q: 'What uptime do you commit to?',
    a: '99.95% a month for the control plane on Team and 99.99% on Scale, with service credits in the contract. Runs already started keep running if the control plane is down; only new starts wait. The last 90 days are on the status page.',
  }),
  Object.freeze({
    id: 'limits', tab: 'Limits',
    q: 'What are the rate limits?',
    a: '1,000 run starts a minute and 50 concurrent runs per project on Team; 10,000 and 2,000 on Scale. Over the limit, a start waits in a queue for up to 30 seconds before it answers 429 with a Retry-After.',
  }),
  Object.freeze({
    id: 'self-host', tab: 'Hosting',
    q: 'Can we host Lode ourselves?',
    a: 'Yes. The runtime ships as a Helm chart and as a single binary for bare metal, air-gapped if you need it, licensed per node. The control plane can stay with us or move in with you.',
  }),
  Object.freeze({
    id: 'region', tab: 'Security',
    q: 'Where does our data live?',
    a: 'In the region you choose when you create a project (Frankfurt, Dublin, Virginia, Oregon or Singapore) and nowhere else. The SOC 2 Type II and ISO 27001 reports are in the trust centre.',
  }),
]);

const FINISHES: readonly string[] = Object.freeze(['auto', 'aluminium', 'graphite']);
const OPEN_AT = Object.freeze(['none', '1', '2', '3', '4', '5', '6', '7']);

const DEFAULTS: Required<FaqDrawerOptions> = Object.freeze({
  label: 'Questions',
  title: 'Asked before you sign.',
  lead: 'The questions every platform team asks in its first week, filed where you can find them. Pull a card to read it.',
  drawer: 'Lode · Q–Z',
  cards: CARDS,
  count: 7,
  open: '1',
  single: true,
  askNote: 'Not in the drawer? A person answers, usually within the hour.',
  askLabel: 'Ask us',
  askHref: 'mailto:hello@lode.example',
  finish: 'auto',
});

/** Tabs sit at three stations along the top edge, as a filing clerk staggers them. */
const TAB_STATIONS = Object.freeze([0.04, 0.37, 0.7]);
const tabStation = (i: number) => TAB_STATIONS[i % TAB_STATIONS.length];

/** How far into the drawer a card stands: 0 at the front, 1 at the back. */
const depthOf = (i: number, n: number) => (n <= 1 ? 0 : (n - 1 - i) / (n - 1));

/** The index printed on a card: Q.01, Q.02… */
const cardNumber = (i: number) => `Q.${String(i + 1).padStart(2, '0')}`;

/** A link the Ask key may carry: a page, a path, mail or a phone - never a script. */
const safeHref = (h: unknown, fallback = DEFAULTS.askHref) => {
  const s = String(h ?? '').trim();
  return /^(https?:\/\/|mailto:|tel:|\/|#|\.\/|\.\.\/)/i.test(s) ? s : fallback;
};

function normalise(opts: FaqDrawerOptions = {}, prev: Required<FaqDrawerOptions> = DEFAULTS): Required<FaqDrawerOptions> {
  const o: Record<string, unknown> = { ...prev, ...opts };
  for (const k of ['label', 'title', 'lead', 'drawer', 'askNote', 'askLabel']) o[k] = String(o[k] ?? '');
  o.askHref = safeHref(o.askHref);
  const cardsList = Array.isArray(o.cards) && o.cards.length ? (o.cards as FaqDrawerCard[]) : CARDS;
  o.cards = cardsList;
  o.count = Math.min(cardsList.length, Math.max(3, Math.round(Number(o.count)) || DEFAULTS.count));
  o.open = OPEN_AT.includes(String(o.open)) ? String(o.open) : DEFAULTS.open;
  if (o.open !== 'none' && Number(o.open) > (o.count as number)) o.open = 'none';
  o.single = o.single !== false && o.single !== 'false';
  if (!FINISHES.includes(String(o.finish))) o.finish = 'auto';
  return o as Required<FaqDrawerOptions>;
}

function resolveFinish(own: string, around: string | undefined, prefersDark: boolean, tone: string | undefined) {
  if (own === 'aluminium' || own === 'graphite') return own;
  if (around === 'aluminium' || around === 'graphite') return around;
  if (tone === 'light' || tone === 'dark') return tone === 'dark' ? 'graphite' : 'aluminium';
  return prefersDark ? 'graphite' : 'aluminium';
}

const esc = (s: unknown) =>
  String(s).replace(/[&<>"']/g, (c) => (({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }) as Record<string, string>)[c] as string);

let seq = 0;

function mount(host: HTMLElement, opts: FaqDrawerOptions = {}) {
  let o = normalise(opts);
  const uid = `fq${(seq += 1)}`;
  const root = document.createElement('section');
  root.className = 'fq';
  root.dataset.block = 'faq-drawer';
  root.setAttribute('aria-labelledby', `${uid}-title`);
  host.append(root);

  const render = () => {
    const n = o.count;
    const cards = o.cards.slice(0, n).map((c, i) => `<details class="fq-card"${o.single ? ` name="${uid}"` : ''}${o.open === String(i + 1) ? ' open' : ''} style="--k: ${i}; --depth: ${depthOf(i, n).toFixed(3)}; --tab-at: ${tabStation(i)}">
      <summary class="fq-edge">
        <span class="fq-tab" aria-hidden="true">${esc(c.tab)}</span>
        <span class="fq-no" aria-hidden="true">${cardNumber(i)}</span>
        <span class="fq-q">${esc(c.q)}</span>
        <span class="fq-mark" aria-hidden="true"></span>
      </summary>
      <div class="fq-face"><p class="fq-a">${esc(c.a)}</p><p class="fq-filed" aria-hidden="true">Filed under ${esc(c.tab)} · ${cardNumber(i)}</p></div>
    </details>`).join('');
    root.innerHTML = `<div class="fq-wrap">
  <header class="fq-head">
    <p class="fq-label"></p>
    <h2 class="fq-title" id="${uid}-title"></h2>
    <p class="fq-lead"></p>
  </header>
  <div class="fq-cabinet">
    <div class="fq-drawer">
      <div class="fq-tray">${cards}</div>
      <div class="fq-front" aria-hidden="true">
        <span class="fq-holder"><span class="fq-holder-card"></span></span>
        <span class="fq-pull"></span>
      </div>
    </div>
    <div class="fq-ask">
      <p class="fq-note"></p>
      <a class="fq-key" href="${esc(o.askHref)}"></a>
    </div>
  </div>
</div>`;
    root.querySelector('.fq-label')!.textContent = o.label;
    root.querySelector('.fq-title')!.textContent = o.title;
    root.querySelector('.fq-lead')!.textContent = o.lead;
    root.querySelector('.fq-holder-card')!.textContent = o.drawer;
    root.querySelector('.fq-note')!.textContent = o.askNote;
    root.querySelector('.fq-key')!.textContent = o.askLabel;
  };

  const dark = typeof matchMedia === 'function' ? matchMedia('(prefers-color-scheme: dark)') : null;
  const applyFinish = () => {
    const f = resolveFinish(
      o.finish,
      (host.closest('[data-finish]') as HTMLElement | null)?.dataset.finish,
      isDark(host, dark),
      (host.closest('[data-tone="light"], [data-tone="dark"]') as HTMLElement | null)?.dataset.tone
    );
    if (root.dataset.finish !== f) root.dataset.finish = f;
  };
  const finishObs = new MutationObserver(applyFinish);
  finishObs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-finish', 'class', 'data-theme'], subtree: true });
  dark?.addEventListener('change', applyFinish);

  render();
  applyFinish();

  return {
    root,
    open(i: number) {
      const d = root.querySelectorAll('.fq-card')[i] as HTMLDetailsElement | undefined;
      if (d) d.open = true;
    },
    update(next = {}) {
      o = normalise(next, o);
      render();
      applyFinish();
    },
    destroy() {
      finishObs.disconnect();
      dark?.removeEventListener('change', applyFinish);
      root.remove();
    },
  };
}

export type FaqDrawerProps = FaqDrawerOptions & { className?: string; style?: CSSProperties };

/** An FAQ as a card-index drawer: each question typed along a card edge on a staggered tab, pull one to read it. */
export function FaqDrawer({ className, style, ...options }: FaqDrawerProps) {
  const host = useRef<HTMLDivElement>(null);
  const key = JSON.stringify(options);

  useEffect(() => {
    if (!host.current) return;
    const block = mount(host.current, JSON.parse(key) as FaqDrawerOptions);
    return () => block.destroy();
  }, [key]);

  return (
    <>
      <style>{CSS}</style>
      <div ref={host} className={className} style={{ width: "100%", ...style }} />
    </>
  );
}

export default FaqDrawer;

// Fonts embedded as data URIs (SIL OFL 1.1), so the piece needs no files and no network.
const INSTRUMENT_SANS_400 = "data:font/woff2;base64,d09GMgABAAAAAGuQABAAAAABCzwAAGsqAAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGoJYG4HmTByYGgZgP1NUQVReAIgmEQgKgcF4gZ8bATYCJAOPVAuHbAAEIAWONgegCQwHG9j0N9DTbgj8uhOgWv2z93rAk23D3t2KiUqM3IJxzArYOACbve6V/f//JyYbYxiQ3YGanysr114ghCYoUHCXyF6CqFW8bsylwKUhpOU/D0Hbkel9k6z9c5wx8iV+4eoM8XBCXEpzq1SqUtWAe2SpNUe+seRp0qFpzsuE/U0wLPJc8Aqmpgx1/5Sv7tSvPtYbxlCwmkwunhr6RTiNujjbb7caT+sH9dEcbvE5LUaWW8GPBLyEBlc3H9UVeknnqad8jXvwxapgNLeax061x632u0uYWN4TMMG/7Ma0uaDJpr4psrkIbFzGSFaSkxfi6f/e/qtWbydDn8lAGeqC0Nd9AL5gpY9ozv/ZuySNQEgcQoDgKQ2WUgpt6qkj9qgZFef1V0SBmmNWB0+pI5oeSbgAQbTmnwctHZ7m9B/tNghQUfBSIOLEiNhdcprcJRdTSEgIwTzUoaO0+2tZZ1R0VCb6a2vXmf9Ct/3OxPjn+/ueXPvc16NggzRod/kwgTSNiUVDAQn4BJryaMpDE+CM//ifcxZfCd1QyPBPRqBE3c6zdvsfnen/IjDKOmQ7oKTg1+k2FSiowiovVsHL0JFAFwT7PRUoZB/5qUAqOyUFSCEfga6AAOJVxmLgPcT5mvPDLe1Wj6VW5TE4yOFi+baCv4INt5E+QZO335QK2tlE3YTf2ZEh/3bcVg4nCiAASnZ7o/4kmQbggVmLNoQhV6u7w0lsBwAq4mD7EnoVl6RNknjgYRgFZIcq3K0Rhgk8AExyDvXo+ZB/et9wGRz3ujjn9dCbezFgOABk7cB71v//3Qd9gb/+3PPg/XvWhTHd9excHQ7ddlBIKZI0beI2alwhDQhgJZB/MOV+jrbRIxEINoNpmb3+D/AHWAD/BG6j3QYi/ClYm1c5y27JOuj2WIFDhBmNba2BpIUw2AnLxwAO/1J5vFI3rM0ajIv+PFe/ey5YRCMyhwEzsPz/N7UsrctSqcHxv0stTo9snRFON+Uhk7eJtM7Zwv9VrH54/MSgIffrD5Zt1n2ieSh0DWcXDRmCHINhy/tovYlIyGGgPnt4IM/1ku+jqNeb1EXGhRtuuOGejVOFe/IN0mDh+ZpW0mm90YbW3dlalasd0mXqA2zWKXYZGeADaLa/5K6bPz3rECU7oxT5aZ36Fo1DJGjqsAk3MmT+P1Wttx2GICxwo+RN2st21kW5u5LkhZCbfjB/oAEwAAkRkg2RDtRGKr3oKG/AgNQ+iOLzo3QpJVi+JF+SLsRYVCnEOtVXum4uF9UVZZGosJM3A/KHD+S1glNT3/xwlicFC2CXxmgW4aiOURzh3t3nTX01e62PzLYbhpEqgsMqjD7LqipHULflcJq9+Pf/36xeLfTQY+v51bKNZdQYMSIiYkTEkvt932NsOTZcRPNKpI/kmZulOdMWAAOEusdvGtl17zcBgrEfMBxwEBEGUVKivDAGPhQUEAx9VatRq069BgMeBUEBmbFtNRwMJRoo1sgUs1Hu6PTjkvbgBberRqxmjPjQLYVggWBjB2HPE8LbSAh/YyDGmSqPAF55RErKI0qbPNbYAXFaLMQ58RBJ0iEy5UDkqYXQ0kEYNEO0aIHo9B7io/8gBvyFRGgESF8NYM4ywAITTQTzjndBEhrAJe0GB4EBDAD6wcCvAJ0tUO2wKwAyrbYlf70RQIdcmAXb7RAQAYtPO3rzBlgMBYAcOIBg4Kcev2kD1P+HnYDKLy/WU7ASSEqlww+eUw4/Fzvl4FFJgwPBBFFBfWcjdirGglWSovwYNjYIEz9KCi5kFBCbZx5E7yq2HrZ4OxrRN4RIP3TRPl3+T/+1f9oneU0dmeAsgGG/U/wCP8J38O3gq/g8PokP8QHewkN8T9o4uqwngPDgAZnDYUPnJcTDHdr08RtuDBskzB0cjBzUXOjDVAPKPxAFeEo/DSc95DhnMYkMaY1Dp6wBVtVdfg2g6hoPLZcQOJ9KVACWiqZadRBart/H9Z2KDLTj4OnCGiAk68IdF44b4BWvuGwuj4qUUMJFCi46Hug/RnEYDsBe2CXYDltgHVZgMJoL6pdFEqB/eFtbNfvxQGhL3fP6utCnNwLz0/+TvjCKteoe6LK71C5+za8lLvCQGI5vPtjtBnQXYD6YaE55+7gujvwgvv59OqrDOghbusgocX9V0vGAbgBzNpWMf3tkV4hzBWOw7Xt4+23rQ+S8R/VBW9sIkNHVX23L+WT51aRJncMr7QcUdrvtfcUroTnbzkY6VkRVe0s9kl7B5nPtaaC9gecw++tL2sHVGRBoG0yyPqz1m71CMrbr3659ox3banC8nBGBwNlc05YD7Vjkw7G5YWAAyuk38l+ov+jlXTAtidmRKRgP9S0JR45tNJIY/UoTaBtcDOIw2WWhFP/O5+rhzakmYvWqdJXd5Ol3mp1YccxT6R9R1NxuzGa85kPQxmaPjc1rzQozezEfzNds+rt1WnH5i4V5ObaICCw0f9XA+YLFC7jh5GyFgHtacjzOjGM4eBgbzqMOET1cumah8CX2E9D4tt6Ejr4ZOODGEEHoElaLKsPLuqTG2w/DzpyQujm+1uqd+iqOb4AlvlfZJ48m3Yp6TanVQshOgzBuH612qzEDXf6GWllLat7xtaASHas3La0LAeoC69VQev1f1TfM/i77BW7p+2jVln8H5tsJJkhmYTTg8Qj/ZmJ1aUh/BWAw3TAk+hixRBkDOnR3XwyEpmNz+u1WPvh8s6J6/G/w29f1SpM0D5Rzn0xNNsqfwOFDPJ6alqXQ7eSLpPtm9xWUjmnXomsXDe55xksvpoJUPBTK7wUbAAHvkw5+BVLtWnRJQWlG0Ja0ndjpfon97Ge/ujrgqq5lXPmz5wqIW//rZt0Fmrejv/6yQxdfydJv+foiDdAGB3XqRp2AE079bQRsAVEx44rqHw2p+MgCYtcfBKt0vNhevoXt54zKtLUMUDPPfvsOJzsPtTsLiAXxyyRIKzrOWe1SY5fYAb1nTkhBnVvHGWeuIlk6j80CQmqtGsz/ksxHe2JAoKwulRU9LFiwMMAqWNaQ95ySzrAFiFZvSoNfOroWZywgBQ0jwggrwnbCXqg4YwHRDlHpDbCTo+ZM/xEBS1nVbqqmWg1AjX/vmUlC+Kt/gWk6jZnGtP5ESl4DvxgiB43eaTSIXszkl9ibLEBAVB0FWMzl59j3T8jKUXOmvwBSC6noowHonIvE+T8hqcizgBR0egRML6YvY8z9OICkLNM3PyxAdnpEq7si4AhHODKsS7PMG+zkaLAmh3Vm3YAh1s9rArCwQcFwNMDYCDCfPRwgjkskUMQTSilDi2nR4Sz/k2L4gJcAzwAeAzwAuAtwy4e5zlxhLjLnnD5NHisuXWwBcwH2y/eo6WYhau9TDUU1ZbpVavq20Ec67fzkNachWYM4TIsYmDPwuu8UBnSwHdZ5TBAYsHunbzEIBdjmR18/a9iB3NwyuDhrNivNo7Ory6uTi/2O6sOP5xPVUYNN++8HNhQMgE+nr0pzM1NXZwlE99YXARYoADDMQI1TqvNzQKiC1EBtlrqToIR3v/lru9urgVB5M7mSKWbryc3FSDwWiXSMhnvXqxOxxYVNpCCXtmJAIhTn2DxABLoZlQJbGqoV27sYYUKDSmGhse90XreYBdPxw0Pz4h1R7fS2f7spo7+qHBvsgOqZEUlFutk/0nv3ocOXsFUocdCYYP4elD1Rgk0B2eurfqZViXfLgQtV0tXt4dnd6/XywG2g9GRztY7vJEZz2Uxfe3E+VQM22i92IG/25tm91ZDZO9v/pqsOr9o4f3cnT29xIDIPiA2sKucX5asjyTCaNTe53BMsSIIRSqOdwi9Dr1UUSejH4ef5nVgc8ycpCduNEKXGycaMO53D6DZ5sBl5kkuyDMXi9Cx0+XP2/PzqOD4gVfaPark0D5gek0Mj/bVYCRSSzCEeHiWZrfbGKMaM4jPfY/p0QNyZ7DSxWTbfrqObsKZXz84paAn1bnWwV3djPIW5N5otL1/uJ2ZymJyNbqBHY4PSC/T0XzX3xUBtLMguBUg11kmmiwpRanQ4IPZiJwqUXqmCP/XN8vy4IqSSr0VougEQlT3SgzLhqJI1AXK37FHn0bskVm2WyeK1gOOStJVaFBoWaRLJy++0gjVnAMXDwdjq3rzqNbxZzPf0xtNSYKX0ApFNkwaMYmtu5y15vkZEMlKd6JfH7W2A0ApSN54Xtsub0MLeleiXZvrPiIHduirCsxu2IuBAi14XfP5itqc8OvWxkKLqrxsKGvkHeoO2aDVai+YFnJ6+eKFbcegfPLw+vZmdKcpDOyneyvZIPs4XJ2OdPdDsABmsDk6iQB545kdJTvkh8tRBt/ysO/bdzo+4wviEZ4zDUzqbcFviZ8mQGt23j/pFye2OTWwNF8q758XtdAZEHdhmdRDRIpcz0QlnM0soxyFetescoNZNBckEG2aedoouYMarKe3sbJTl56keR0SiW0sroQ1+LZNKMqeoboaHaoTGNihtgVppbcJQyUC+Bxtxhe0m4FHm2NG00iC9kqIidPpib+6qSm04v6KuzAvQ0MPVUlGlZGbFE9iNw5WwPRDrBUBhuEL02GZdGEdYRyfRK3KM1TjMlqeRNgCRTinUsjWZMGA1W6sXCCWhJzImVE2ssTlObTwS13p7yzN0iEE5bB304uOL3l2M4Gx9aXiSP74cG6zDpIz8YTx8cD1c6gATGB/ZxFHrOLReXC4/3H/b3tLyvd/K/vCTw86jbHbl4x9VhtUK/jtPed937junMGvXEimm6m8B4sfozc+1aW6RpzrFc/h29az68MZENHnbSj1KYBsbE0bKYZZHqsB+8NyTX1QbeRcAEAKxlW/fhL8nqAtfXI9Zw2Yrqc6T23L/4NJSxFSM7RYeVJ3WXye5Brkmc8Pu5YzcF3K4F+s02PYEmz3E0lC1VItTVEY3CqVXAmiQlyDDi3Wcj2eviuXtobbA3dmRkzOBAm3S4wMtNrZf6eqcgawYbNq7ylbianr+tTUnii/hwAm5qItFqL+N6HQ08M7fKYIiSXAZw+7XXGzUlIZVIpVyMx3NYzVbyVjETjLVPtrgoZUSFa7uXAJgwzEV0+ihDkkbal+F3hFYgrWxurcl0Hcvxcoz07cjtfnlWD4WSyOzf8eU4uzZVH6wNDb81cetXRnVOVmdJlBFur0V0NwbFj7OkC1ZDLhxheoaBohOUT8BJHaXOntrteDRHiYKqkSy1go28S3dR208s1g7pKmL7NqTXVzfepn0791KdQTqk7loLIoyxo1i1tAU5316+6ELmFik8F8WsTljF5KUKL8si2NY1d+MJzCwk1G+KIPieFnrWblMams9nDboNfkYni8mvEdyTGfQsOreqtqsO9MYUVVoqZllyFurzFw10HxSNeooeLwmUN9qeHAiWg0TJ44vNEO2tjQKgVM1+FXduFZVP2KT08dhF66IMxf356oaz51VTWN7k2ub6Snx3pYa8qvso7lQl1YYd53dgZ19Wl0MrR2Th4IgF0IqT/cMEFooTloogq1mihLKyeoAaepqzf21ZpcpgS1zsn4wurI3udbwRe7uWKBiWNkMG5V3ZiPTmfaP6a6Ex7KwvtaU29DJIo5zd04OZIKrx4GhDFP+y51r61v9+fDOq7u1+u/mR1taCju7mQ//FLJzPTty47MPZADg29WvyYFJUr71Z/wKJoOT4Qh27/0Ty15jtgeoTpU83e0d1YpVrQCvL/PVExH9ZsMKB6VUfHXiuJAVDLKFghk9cCeHYeDnlNpUwKshpZjE0C7OyY9R8odJ83W8/Yk+cEjEw3NPH8exeY9SMeLx22N6EhsFFvzvsM7P/thhD1pxNvzHv2w9VCGh6Q/OQu+uT/oZPQC6IqLmGISPiNdwLAZjObi2dRRyW0cEd/QRUR+QWS7vO2Hq50bL7qil2fyfsHdrPc6mN9YDcm2ygHRbH7QwT/4/31+UdGyvgN2PXk+A1HUzWKQlJIiCKidPWt/2DiVdBLPqyouV7eSFb0RCLjr+6edp6w1HNklEo1ueAWNuLxSPn2b57Kub91rdbSpAAswc3uUFe+5YOgk3rBo+e/WYKma2dm9VY4LremZ99RrlaLo5mbO7V03aR3B1+C0mrJVDubD+JvT1BU32ovbakGqsVO6wqTUS7SG72emH5cVSDD6auF11wuvN6llSzTPF7QWDtnHRXr33ykOvfqfzyyiDTXlk8xnDdfHUC7WnoxVy6xkfYsJScFgi2PJ8Z90pW25nJZMMi6XcJFQZXXEbJ0pUQ691rMuMIEKfi2ENcYMG9dh2txuXypTkEsakX7h3yAPCWbhL/5KYGDCxu8mRYU5dsuGTUQyTTGfh7hq5WLNeLD6H0rdzmVkDqhecAiS47VAs0wUhgpldLm2ajWMCVWixa6anEo1k8SjDF83liNFQPqSvAoS5X+JZ5MC2mSjOxiwwUCx1E1QSH4TaibZTIyGfWa2jIwrQXY1pgUdmQ3KE71Q0A6zqdhAxjmKQqY3fVVOMk3a+fvPleL1HfpY4CXd+Qe7u7BxlgHk8qOuJOa8Cmq9nP1mfsnt5UKt2q5geLBv66Bhp3blQb5pPq6ehiTCLdiqfaHAxHD8pKht1MtbxmGGdwYtXICEPZ4AxCscdEV9IBHd8gYpeKrAeKr9yphfsrovJ/FFTp8tLXrpJTaFfG7kvhSan+c9KINqmaRwyjahpkrFjhiaA2NxxrYRcLhho3cgzL3umTVslgi5W3UqofWfPpUM24g2VE9TDSOt7j0JUQoNxAgmcFxNO5R9seiRJIWY6AFKkBaqHsuYtHV0tekMrS4Dg52JfcdVFlrCNP//KgJCFTADTGHja9qjesYRg0YLYheIaS1yLoTBlRTjt3UOvlsMOzxKgy7xdWy1LFJOiowVq4Lua9FXSxK5c3nb97agyjFf+yNh1X6mdPQDXRAs4bk7ZnPfzme7BMbIKixgk9OJUmnwFCgzewixtSl7oxaUi1cw9DkQncdJ9z04bVHm737OtH+HmzyeoGaOihJYVRkf7yxjV3uDyQma+3/BCYuRlx2yLXtqzjwOKjFOpjAx8E6jm5c2qvBUGj6c2kDrscVbKfbfLQ2a/3r9Ad+UDV94rg0ExHsjm+nIrgY35obGZje/NLYy0vn79f6tq6Gjn+9s3A0hsdglXzLGEQa8yNvtUyebXNFQKci2plEsNfmfvdt+vp+Hny0afFrE/M+BxPe+3PDzXbfwv4VQqtrOBydGlnxJC1/P0/3wd3Hjz8XC1lUsjUJBj933Dscf9g7Q9f5sPMVHKMmnzRUuOxufHWCUmuqUQtXtIicuYroMp9JKbecwgZWX9qtKYjPW3BlDm2Rk6i0TrbAaW3auMGRhL6g75ljLFHgtrBvHEskJAdM5etpshnsTDG1UZc0HXjwIElilbLCVxL6IUDS1eWTgsWEzCvN0tHVgU03wSkjgtBiOZHyuj2u9SiaXlrqUeIepS8bbjfcXkD6e7N3pbd5ZHEDrosspbZdxtLnT5fHIhmprqSbDKZPLICUgNZNrR3RcIhP7f4Q8fZZbeDwz+bGFl8c7oUEfH5uhGbmg38Z17tysj6ejrrqe36h3onWxOr1Ck1htPBqhyPVgcCcJDdSmU6oz1aa1PMencg9TApIwNqSqTRia5TZFLOiZVvSCyXTa+Mk7nh7O4OkVMVbPzrsD0F/5KvupG2aN7WIlnC6dSg/fUV9sebEOmK9OgNn3eL6CwU7u1vEJhITEVdiw3LvBDRhiqTMSSrEiTprNh7agIzZ8p8+puvyyELdpCxU2jzrowR1IFsmqntJ35s9tocrKqhTNAa5SntK4TzzAuPR/rrTaiM9KjQC2WA/GEd9uKGZ4cPwuD6MS4xMrbE0ovvzQ06m8OkM9fiPCwOptOz3wtkJGN3RgLYmxp5cTWtbaPQvb7ZIPPds6dbcvPDg/CwqcMp9uIwkpspxvmyfbzPTRNircdOX9FhsFD0vEjquQbKac3FmlA/anwBjkcDAwnYcfaegLX4+n+r59x/We7nh263pIBiZ3r4a5VhPEM6eZy4nr6OtqUxujd69cplZvc+N5Hsq7nugtIkKFAkgkLG29dtvx/3sC6P9UK+nioQ6uP20ygvc7CnRGzDi/GBJCggEWgWyvw8H274FVVCQqP7EiEG/tMhPbkqu2tqTR5NlNVm0683j3k3IscO3t91ddsYwyjZ7DofTVqpYrd6FltpxuJyFyzONF+YM9eFFaF0GqdFTv8eiA2PwCp7KQj+vsiGRa63OLygumkQWpIMddijNQOVd5gwHFMKi0vIvc7deq00iN6SmY/uSg05/we8AhXrUY7DeuIYi3rXxQBoSywGWmcdm4ZSPaOzG1PTwQbre+d+OFCwdqb0MMEHJfZW+GWJ8npi20v1yiRtFRWJxK6PEtk+x4VPwBZ0FVTmkllrQW+lbWp7MLMVj3MPeqb7SKR9dBnMs4vy0QCeC6eqhheZx77HzRn2+UFhMr+OppXFHJp07cbSn4JxkE2TTDb1wCbOF661W5xMRAO8W5rwdN4cLFR6Goura9lxsfRGBae35qeKudSGDnHsJ9+r5jgl0n8AlbbRxfCZjNq5KUnAOD8y5X8PkcaRdopS1yVcNmUs7L8mcYkerlgUkklJicCVkyPDUlSOVsTKZX7m2i4wrQQ1PCoUHtStexgeRRSripP9w/f7Vl4JCrTvyYHPqzl2RZ8IHuolACPoiIaa1vYrwdAzK8h0bgo8qHi3jqyUkA9mNB9l53M7kSFhlnoFlIOTkU0upyR8flyfjIQ4TPxqBKYDDCLHm08s09gLHcR6mnxkAc1FklsN6pJLaIOcinHKaX9T9obiR1n1mfn4ref415NDrvHv0kX9q7G/GtTIsPGVuK5YOWUahu2FuuajfngabU0waxkHWktrl+qKecqSnS6b2hITWKuAUyfZWygcAv8Cos+NkSH4tJEY8YgEvYiwVir/Sdp1Qb7b243liYwldzUpMkDQ/GTKsy+3Z7G8OB1/OmbndfdjfH9rM8Ptx5jCFF/RNvPPXvb7cHDVXIyzV7BCNb4y6MlBDtcZzojsaytF86LbWoHGpEu809Qip21O8X4vxdLPPk0vyzteHK1JPlBLtIih8LQhLY/6emXtwydnrmwrPfz8CnB5TC7nLkhvcjTfUdD3ay+k4WkUEgRr+WCoB//8EDdY0bDXwPe812Ss13BShNUGA7W6U7rsBEgamvH7u/qUq/vm5M/Eb/WrBqbrX6Tm+ipJUnUbsXvyxFa17eKDwhwch7CQ+n14vpHW/SotQf3CIvuThQavAdBQ3xgMYY3oSk3vWgdro9R+MVpThW/2hZ/alC5ZGKlmpjPfo2sHs3NRBplz39vpHYCudhYA2SXN9mhl4hwS21saooLQHUsaWcjy0vGJjbWxs+7Wpqd8Jgh+CteqzNY3iMPoEHeluLdm9UpO952rA/FRC5bzjSqk7Tgw3sDfV/Gh0cSG1h7//sbvtWab08uzvVvvAoWC8HG8jAKj67hdUqtq4wOpLwsraVQHHW0u7iGBgQk07MZX6VyYUw6KPfHVehI8mjDuKEsxAoJ1FKsK1IzAk0X3QyaAFq2UP76GptweM9SqmCtHreA6dZXKHOBrsaWTHewaWS8Xrlc5snHbzoe9ehibenOf7h67xgzDwgoeCe5PbEZmztQNuh6hfTursl3psLFipMEU5tYCBW6YTBzchL2wwNXj6/swePleVVH48cNQ01MdNSjlxKsrDbhDbnS/VXNXIxlLvZA8ZjVdf/dLMjw6J6cTNJLZZ0V5GoZNPNE8N7Wjx7sVmpbRZnJOKaJsCq9KLDaxojOoMrmW3XEbkdoLKZp1w8XBJ1RANp4JOTwOZoOYGKTfu2OmbYXrkz40GV8eukFLE76/ONDUgYoTRTIJOrJfL8SULix7Ex8zs37cuKiba3K766+9khLV8fd28THU+7LcdQ3ZwVn9D34BJUjFTar7WPn/wB7UfnZwOFXR7752L7v4N0H0n4mVJherp070I7M/21DdPt5u1/Iy5OXtHxs8LV5+mpvXb4vmOpVVk8Wu2SXRFh6FN6yepLMw6axxC5EwGu0Rr8VqgcYK1ikYVSr+RbfGKwHoS+iJ9fU46C3Bf18XpEHl2RfTDmeELgKBdTZXc/Ag9Gfqf7IzItw8Hw+rITpCnQF8aE3T+q++f7roUHKSqbjH0+85qsxm2/rN+XLLoRQ90HxDydM8TPItoVKkllfW4IlU9AYr+hLD4XTf6fyPxigHcDa02/aZscSw/3B5d6Otyojwc6TJ2Z28Jj11Kzo7+77bTnSBhvq2VyUFv+9ll5OZXc3yrN9KL7+HV5SCsPlnP0/ZiM0tb6BLNptVKFNTJjIKuebWYjW86jMURr2jdCTflwsxN5Md743nhJBjXMti6V3OqA771tUorbnq1N7vFguqBRzUfZN8cnySacvGTg9STnSNbsD5HTgQCtB9lKlnXmJvdTkSVw7iFiOpu38gaJJ/ov4Irz9UxMdriR7MR86vPw/kZiXSfJscitQi74+lJjtn9qciuq110hFaLDxPMJ6unf/EzE8/UlA8PXC46FXreeypt0DFwtORAYoC935XwWdyEClLSjMr+Ijpa0Sb8F05zzMb78ZuYj6bWXPEOxOEwWHMjDn1TzFzubowNjVB63VJ2Hbhcyj4+L9OwkudvCLXDa2R2odXFZW+9XNXPywf4XMz/MDTQzLLRqO9BgMmbg75EcmdnOWtu+Ull1wuiNuZ+r+c9stZ+abNnTwaVgN1lP5aRaa4ljKRjbMm8oKsTe46sSGq10hOWH9PTiZk7bBXnWwkZlEGFXZHs2eETKRh6TPEcB9p+0Wi67TuuC68i8G7HZf1iVN7nyMMVl9wHzJ7VPRLDVTm+t18rbOQ15mDGVb8J7aX3FGtiY8kGA69c/YOefZ/Sxm1FXl0JX62+LZQlq1UCRJcnStv/nmM4rQaGfGH/E0Ub3kW8FfK6xrWkT9zMa21asdA22Sln9VyfOPOrKoWkpFdekVZepxGkQBCcesSBUD40hN0L0Q1FlUmVEdQ7+bZo/mc3gXV6xs1STOrbLKu86PT0d5N41CP46es9NjRstf8diu6C/nLpsqf7zkw+AKLsuHy6NWf7msnqVKVlWlVDN0eVmtHhMzFS1SzxeH1SVe9Jb2CI9vXD4Oz5shoojKsrXB+eLH/Znyesijyo/Tp0mbHnbKZKsFSPHAU+cm7UfCg5BC2oJcBEMhnIBh6O92BR/OfI3kYZTJGkxFMpjJyyzSKNKY3da5SZojMuW6Kl+JFM+UuqNchUeq1chVp1m+Fu1e6dSpQo9eld56r9rHONRVGIOPgaiIN8SreEtSvC0r3pEX7zov3nNxZ+8TVX1AVvcZxaovNE6VfmvWQVcrAzYM8aYixqyMu+WOhJ8fOo04kxFpYzw3wIwBhBzJQcrqtP80gkVk+Xr1d4x7zeqZaesjKIQJR2tmloydWToyGDdfmWXWvn5ISNWgLdYXtzM4WEUT66F9euJqoATXiAoo1E5SJrf6RwGMn9OmDRtTmsPmo5KE4j2tMsnAGEodFwqk+mgO20lH62aGDZ/ZZVgwXvc1K09UI9kq7bn2kKY8XH/+4n7PGCQuNt0PHo5/zgAWbt5xhzWrF263YtNOQKyfjqkGBgRbRwDLsL1GCqAZhGlf88pVsA1ibS/aed3M1twtQMvd33KOzPxt5fops2bTPAC7YApu9R1NJoYC9FZfeucP6YBb9AWTjmx9y0A10MWaoLZV75mzv3W9oMMbQm7utrDd4NZOiYWpfLRyZvuxMzuMCMZFqc+kRS6akc7SWppJlRyqnnK/b5thpmwiJp2/ogMjZ4wC0YJ6pD8eix50/Mi9QEv7A6sMrDZR166GAUrrlaqPDu8sdL48A8dCZp71CQrlYO6xOgOgBoMh0cGTtU9P/GqrUWDT9kzs+QAA5AjVlUe3b/xY25FmVTYAvltP3h9mlQb6Z3i2kEazpKW4uSQ0c2q0wm80Hz7QTMZsgJ3Pd0zNDgoUilbcBxfczb7ENVrJS+LmUpsB7EqHOgC70Xoyoy2U6xeRG05+wCirMqa8aCRQwj2AxYXgJ8nAcAErO8FF/6KYvcii32To4G8rbdPY5Nkk29yy2W3TakNI/5C6pInS09K90lFpv7RZGrb+zppribKOW9dbMyWXmkubV0nCEq9ELlFIXKwolrcbqxuLLFXiQbG83XBX3DkHsZkoxONjat5iPK22nd+JMkWHRR4iuchWZCnsF2IpInVcOFfo5d9fDiEhlAjlQgdBn6AvQJRS5bAgSIAITAIfgZuAIhzk/+Kf8jfweXwHvpRnSFQnnic0vK28KE/Co3Or8QvcIK6Gq+RoONc4FzgxnChOXFjL8eNIGmy/aur2PfuGfYjdw25jN7DL2E9uRtp98Pulk/1G5FrkJ6Yq0kL8J+6IQ/QS+iPhiF6ihWgU/veNS9Qp6gC1iXonnA+PCHfj/wuMX/AjvkCuIrMsec4bl8hB3INe5Rw9ozNEmhyaRua4gPGjdWuL6d+atqakOdxs+qv+ziWa2mZl/UdN/hV7l2AdVAPab6qC6mi1rrJVvPKL8mkZUx4uN5XRsrEUlbVlAeVd0VwQRXbhWwD8J4lMt9KFtIE8SAgMGkzMMIcNn5hMy4fJDeVmGA/ejJncxwjjTEGysaMw3Hz8AiIQLVKXZquMNlntOnTq0q1HzjpbHHLEUcdcctkNtyRKkiJDtjvuuS9HrgKFihTTKPHEU88891KpFdxplVp1tHT0DBoYNTFpE9GlG2+ueefDPzKffPbFV336DVRlgFSa7nnrrz6e/CtePjQGwPKDOAG8kJF050TFZFRCSkZOXoGguG19yRUiSUlZhfwavh8/Z96CRSuQVaqGoYzL755NW7bt2LVn3yGNrq2jq6dvYGjEcGxsYurEqWuuu+E2CzZjIxxn7sbyZ9nAQRFbwkZC10G73tjz9r55g0sCsSq9LC0yBhk4yBOH2IZZRlhmUUWWEsuySMVvXhGN2K+zvY/c/+2cYmndMXjlhVlSCoqRu7YcGeam9SFbFBk+w+STE5K3xXKs4DD1fyn0TmT9TFEbLEKOovXKFjTDIVNCTkbeLYtDwS07JsCk/ifTiAw0IGVRoes8tminZOcKLHK+af+645psXXZPLmbgYVkGR5qaoQe0LDkUyBtHrhGTXcRA5PICRa+XvI4dbZExDESy8H69EBdJYhZyOq9QVC5pRCLXBRGD3JF7BCzPcI6HbYpE2IKVI7JHHB1QHHRqUE0ATdTd8+wNVIPbuSNXm3deosmdlHBXskikLsXwh8ItqgybTFdy7CzfZ1fV4Wl3BFiKlo+hIC+tIMmuKx45dSzQjzhE9YdIh8iE2BhCpyrHjMdMwPi4ssN1mzf91TbLjgdNYRxdxnvtPm4zrpvvaoWl0vCdFhyNS96ohr7vu9ak1v3okJn3qysn3QITvRaK17Ynl6iRtD7gjQ9e8vaKB6val5ZM6WEeXFCvo5oNJA23sZmsjdK1mT5tfMsX5gvmxS739rwWO0QfOoOFqbCqiZGS0gC0NugAb5hMfdDHvLNxPaoxbiHMTA3bGFGIkFBxNZF1JgXewgW0UeNpfVC2Tjd+2GWv7z5jw0PHPJwQnZp4TqYAXgS9ZHfFw1VE524Zv26tMtK8YqF7JNvUjm0S4gyuzY1cUavsaLczTjqcTjGeXoWuaU/MzTqtdNQwMCQ1DkHu4a09YEEu5tmUt256hl/Ibps7xzWqUcyfVDC/hGCoT6r92AIkc07CbR+/36nRnIHrFdBFa6gJqouAovsttyLU2nStOTcv8t8E72gcsT9CNiVecx87anuReNJhxVFD6Kp8OeHLMeE5V7H9xEuhIYKIjVdFPrlPJi0bCAy5r7i+wolF3Mhqmd8vztvSLWgM64jZTAmjhukPlwaQDaML2cmvNGv80OcBfBGAB+FLuoW1MCR8/yGX+uQAX7yTYjN+DLN1RZYcwEgY7fej29S+nXdtrR3d2dDakaOGm0eAx6zHOmyq9pS9KYaQu678lpMV7w47P3Pb9iph6bhB6q+4ZU1EO4nPx5Z2muEJ/FnWxvndh5w5vgEejaYsmYVtwPae2/6k5mHdhri2QU729XVH1SZid27HvhQ1aVRDWpHBxq2z9ekI5YBxxcRqHz/pKz1+9pOq65v2hriOw2aOmSVAmsJA3iuUohHo0c4Cu/c5V9zX9jyii19llAf4ZiXDaHK8SIquVMPJHqXYostw4hkMU4jFsaZbE1mm6FoMoyuLLRCkVGO2hEP8yPlF4ynLSdK+atbLUhknCC8qv+jFqmqXXBXulDVvzk+mrekcrZFXOWUnJVLHo5DL6DeT5RLuojZii6zXJdCwCkOiD3tN9ToHmeER05qcpyzf9dmCutisrZq1afAkNvS9wVuBoivweXd8p6m6dGDbKsIuBJSsVkKJoqNSjNyJsBTVtvWPiSJdGu7Co0xb4q0Nn2L6CMu7vTm6o70cclf4kBMcIdy+QywpBdMiRpN9yFrPFeGId1P4lj/hyXY7nt1lua9KzQkSQ9IOu7vtI6VBGVigmEWG7q+Au3iaUi3PklGWJz36pKaFEzvmMdMpbw9teUvBbvh+i6ydiWIVG5y6U/X+iZuat/QTecy8uAtuqrJbQhNQO5WwMJlBUA/Q/2ovbYoaKSudflIBvTZ885TZAibsBYrutctxpBCqViV3nF3XFxYd9StYohspA6voFNDjzUCd4/7dfVQMJjHATLicIg/r7a+TUv+3etzur8C9amWVqvKW5KlbywwrVqMTzoMiPYkhGSnAAKGJscjOZHIG+4RzIbBI/S+loXfzBcwqcQkttMF2MhTjWqc7EfoWHWPSv9ggNGcmsBhJc4lgrJPKehfYqjJb/KeY19Y089tD8B0t1EIC87Yq9iIlRMP5+xfAM2hyJKUrX5jy41bRuACJdRIQjuFYXoIlwgvw6jwBh7mrjsy8Y7LYncH3wm24ZDjoIgqV6k9Pq8JRaK6/455JyH/CkUjD6QSEUjlSwV3Tge2zMVZtMQYqjSA1Mcw1CFSy+D6WM0L1rZu4i4kdMFb5kmsBPp4iUvQnWvgBxjmAmagZ+/0ITuEMIRuEGLEgYfnTlM+yNJvDvVyrS8zQDXXk4KTNoa8CdB894hwFKQPFUMmeCMWDzpw2NuBO02cAThkqUT2AGYSVawAPrvqT6DjAE864jH6ChiEj2kXNkhVLqArSJrh9/EOt1MG70H070II3SkLbSHRcgpuQHS3XsOJsiqNSjhEcvE+VlPspRs3dDMEq6TUg457Eol6JUtHkWqfoqASHfj2+iOMV59cyKFJVPeGOyQmyIzXuZMMIoqNVjhs7VTMX6JvxY6s063O0z7++EHjYzohtz/X3W3GGV6z52UjAUE9qmC0qZbmT1ALwqYFo6GLMAeHWUKJHaVw15Ux+0pRcE0qFu73t8IorEjg4pwgqFF8UVY/EYnRYaQQwDykqlNwp+GjRNdlrM9vVEEStwfpVAP4IfkqsYlk0vL0r1gKcqwPIEbsBTHuY+7pGPc4DCayFDVTAuGHCUFBifuK48hXXauqh8cJyr1TGe8K508kCR1X9yPyEtYWK9SmJVoeP3MH4CYuD6bd85wZvWD+F49EBAEejIpaDT4unyLxa4PB53o9qnodSFjIdVhlRiJCcohpxr66P9LOZKI49RA+FdzTDkbJs8tyxTYVEgoDz/kMIXwRDEEMD/A3QnwLVNFvzZPalYtMVRUD1sB2eWNNyo/3cukOwIrDEkykAMfZVCgBHAR4oOIzCoJHFPLwxL+GbJ4wM7qNr65m+HpQSieZht2reQ1QMo8Q7kvduIcYlENg6xF8LtwWeOklbhn4fXYwzM+IyjrG3oZRTrYHrgLeXA2nIKwF5qRDJncRPSuMn8bj90F2ePgaqiqlswjMI73yfBBuliOegncIJ4oTNIYNh8RHponhJakkpwEoWIzUK3NXa10KoXA43b2K5psFFT1XwhAsH6wgdKGG+WuGRONUsAoCIo1znUvH9AFLedgmUQDNokCLY9+gAHn96cyRTBb3f2ItpoOuiu8TTJ2vocf76viQHeJu6wFLjl5xh1RwLuTXA3e/WEQtBKooisik8bAYb8GVxOdIA6dDWkcyxWwY22tV22hFE+cG+HxWXcHVz+tP3P9OJqfz5L6xp9XLQx4OHNMt2frDptS0uWg59Si38wvfeuZ0cbACVx8xxHXrriLvBfywYc7QdJx7T5UW7anGVkEm3gOykJC7pp1PKZer4Fh/X7o3oqbZ9OtW0oECB+rtMiXo5bG9UtUYe9ZBujfddCGd6Ap6sbgw53JDQYWMKXatDcVfcno1Ob/++oP1pB2ccihsrqtbFrd0P2n7USl/QJW1XJ71lYmHzA276Iy6a0QncDtqOw+bJh5wDGzGNt/lQdup7uVjQtU2drB9s+BG4hKt/sWYef87mF2QwB2+XhyZ2Qlf28pqRl/YmHRxRPLn33vpIhn/cZfSRsawq8z2u6nMd+Y8Agt/uTFdIdt/uupWb4m7pDbooZp+bn7CwYnHK0qDlVSuPrfa8x7W916293618wD3+lBL0/HkH8Btf7C/2S5Jflv+KyFcVv2bz65zfdPot1m8DMujA4ywiR8hT5lwUJIKGizv06Ii/IXws9gTVBLU4YodnnG2fSXy8IwyHAJCbinuu9pIsAKH+2jWNX+MmgCYTzoAhqZoHNU8ENMCyCIUkw+huU5nF4zlE9pER7MfhrZ1LlVNfGKs5nYc0Md8ZXr2HOoadFYklSz7uEOPl3UAsy4hzvzP2ZmAMgRakQhYw34VHhKjwxlpUEBH8famBqC0lt7ggX7QOUMRwaVsQnlHyrBI7b2bDbEg4/jngkJ0ipuJfL8bkuy1AmUid0pE21qWjvVzkYvhe6LX/dUYz4MxCbPj49gBwwVpB6EV7dNH3ajUPo8zt+iyHvnwkMGHzWFHtL7dCr0kenrG3/VbiFzt+nqCr9ypBs71lGZJnxT80+JZVez3gXOKKEejFc5gBKAQ1XvEmeB/gYe6mWuzs7DRBv5cv3v3rsIE+SsZLSv0mXVSEe8AVoPUeHymwAsoCMO1g837ZTdkb1B5Nid8tUtW1ix0Sp2O8vGBvRDWFD7ew/in1DDCQy4JzyAFMHj6n0pAPTKUS7iwpE0fXtVPTyxmlyCIQhIGCAFocFMQXw0hTb2i3xROLJpGctJP18mEmZSEApGlxoDZ2S030QRwCQ5YCa8M1nLJWbs08v4oxWl3j+CmpvAnhSEvQk3eqLvDwxRq0k2y5xvE8mkbpZJnkmrxyeSFCg+B3pJmzHBmNqOB5oXXRuaq+0zonPt1EtmRjkTZ3wtWxAwEI+yvl9s9oQo91M35jiwp960Mmy/zhbSdEHG3EtmFu+a63Y2Teh2cvAtBe8jo4sDvu7aTiLX0bNhMv3AfkEAAEA4d1cvn1ZgEHFw+fgJCImCUrksarHvOqx7jq0a96Q656tKse9SqgsH/qdAV/Ol8mWr9Lr9uMev8h25cKtR+7bH00Sp22euUSFD9t47J1KPgsihsFA9FRfpGcWY7agHhnXdmyHtWeW/Hilp4mXDzpVVP0T/Nlhp4RzbMQx1F+vRkl4+T8F2R+tWHLepgFCB8NhD2w72cyXXbabDXZqJOqslYmUWQlZSkSM9EAXl7BwcTAYoZuCHM0QliCp2yk7+5wd2v5sJSXy+t9il+KDlS/O+OKg8XmQlQU4qVpd+LEw95whQaX8wHprmuOihaFyRsqx4Cq/gHdvop6vhhk8l01fewJUlNTHpWZvLjs8TIYPAw77YwYsS642GDtOWTFXnSb0Tf98EP9/jFwUDnmuBNOOg9BJQDNwWlTf5VAKJ7LW7mq8mfhTWmXZ1UkalJJgbMlSm1QWdIMwfekICqyK/+ebZlpb6111suWI1eefAUKVYCBcUk8sENMYL0xLIbagEFDhie7NHLGrLPeBhttstkBBx1yOOYaG6ZlOy7NiCVSmVyhVKk1Wp3ekGbYIJHwo799/PyTBpMyOrpYA/S2HyDUroHHmhTp3Q6joORLZSInr6CYLv32SXPfg4QGa5IZ4oVXf/cq1Khn1OO9z34YjIIYyFdNfoKahBLyPbscczoLcSHCeltstcdeKNAJpgh/aA8OLLFB6h9x5j13zPILDx4FzoABi61/VHcH+oNRmR8YmkaCk9ux7/dIA0H5ngPt8TwJLTlunqPdboedwNpbPOihzMaw054xxlgQ3CnSa7Xo7pzHmozH4ImOF0+Bn027lLQOnTK6dOvxEZ/6zOe+8KWvLLUMDNxxEgDfswhmumMTbheVTtkMvt30lLnmmZ8LkW9Ipu13hp7P+THLYOZsKCkX+aEQqESMc4kB7fUFTpjgIHy0iGE4YQk2VI8syRGXngnotbJ8YSdWu7KIObTkA2yHXMKCOKKBGJ48BTBiXyX0osBwuQN93xjhvtCl7wehgQ2Y5tVLelx7h7JGKdp4jO0GxREWAszGQ2cQstkotagVmPqy3nE9/WPLQNRy2DbbGw2OpgrEK4FRmuq1rCrpLODQJM3vRC+VKPBQtlTxrrkgxnEH7TasV7uUKL88+DLdXinYLa7TqIiiuilDM6E1WCDdORa6wVHHOrPOkUOsdViscUisdlCssl+stE9M0CumSwk7pdeIlF/Lszj7ZSKXa+w17mefHWKXSbHdrhfaZifrrlXE8UzlpLbLYqYdkWPXSSOT6BtUeyBC85T6L55zXlOz6xotXHv1ZTVTeRzvb0q7q6VYo0KVSmWUcuy/bpD8Uur54xlwnWOuV4F+Bf1+sn3oIzlvIMv1tHbxOHQL7TkYL95CfkLjRNtX14BHe9WK+JtZZ5NbXXHVNTfcdMtt8Zq89uqXs6HU393U+qqWIgMxkcg1Cr3+9BsgpFT8xxO1y27HNK9fyWvJJmGD6TdCqF/z32j4Ow0ViFtiNoBdv//IHgEnMY9HfgqcCXAK+f+ObAQ8SvZodHo+0wCk7+QF4N4Ih0LLPf2KEHRwHvucZBB24XGbV6FigAvfr9qMFgH6V2suoFVguAi9hl/3KwIg0pNislEcEB9+bocCog79SDoz+i4oBW/4cSBX48STv71pR87KOW5foLghiG+FdXJtwiWsWpOEtBETpt3opbAOdTwTpkTB6bgZzku86ddfHbial+29yb3pvYHe3N6y3obea7fdMx++S+QB6PEySrwUae7KkafIE5I/WNVyFCixUa2wNhnjpmz3f2EZ6ng6yAR4hTNxXuJMv+rqwNWcbOtN7E0d4K/373LgCIDD78fqW/v4jqFv1/n16/fL0Az8+Cfw488A/PjJn+bPO/5M/hm23Qh++B1EFMBV0S/TSPCBGW+5ld5lieUS6jTYZocf7A/AxkdlVAcWBABil/BGNJoBcDkeJ308S3TC4CBr7MDxUTytXGZnGelcHpbtdpGUwuU1lG3uxruE05eLtX0GpIp78ID/cGvLjAyszL6OK9SoUDOnhX7DzrpSsfBnhHBFnPxNmvX117rUla4WVG8mr7rTBzyr/ZQaKVii06531C8el1/KXuP+M3P234pVCIfDCqsDO8Slw1L//Uvs5d7fvftLzDGJBAYztIZpogLi4rpYPOVGy67Jt51tyVI9TCR6zxP4f5dkkGnUQNSC2P5mPz01Xc/wqA9CtC5CecKBrdYkIwnDUcKoUwiWWw9IvWAnRxW7nKQz0khRwVcFPPwkqdXFB6Te0Gpgo8qvmqMUG2kWqO8plJvNMJYepO9Re1N07wr0EeCfSLIx0J9JtwXwnxulm8s9qt5frDU7xb5xRK/WeFv1L4Q1lPz4aOBBf9WABSuivCl2b7to71+8puffadOvaTNmmy0XsImDRpZ5V/L/WWlf2zoauXjcRr4e9JZay230mq1vrbOCqusAYHyYAGgPwFIvwF8Fhj3DZj2P8BdNXzjH6XqATYknzu9YX59k4r9vMstE1GysoqVtSIazqSDk3uVEFN2VYXaM5kZCPoD0x0460z8g62zVmuoCQ9J9Bc7ZeXaeohqwCrb2oNqK6402VXmqk3saRpCs5qnya2VfKRN5/IeEsTIpJCTkwLdiHVNiE0VuyZZVSWQLrOttvuQuHohUVIlm1lyH5JQs1KwqzsfpgC76g3kbYyqlhrvruUqr5gyxrtOJ/cuuBCcjiESI+C9OsoSaPGSY8/DM544ZWkBwUEvkx0bjTyTfElpoHIdAUd5FowzHGmMGxzUd7SmcusIV3zrynqfUNlRx3PmGedg+FkbrHizxN2kdyB8Nq8bkuOrn2fKFhNuLp57pSaiSY1k4zhBRRpDPRazq00wvUJepgREqMNnyjHM++55Iud54NF0OE4nSfiSodbT1IzmxZ+BeziJTnfApzQVFwQH66Wznthg+JWHR7AYkRh8E2WRnmCHOyV0uEhO8DlFVXcW42VL0271bIlQVlhhruNqUcs1HwhIB7U4RCjgA7TB04+BkcsYS4joZuwEoEItjcIM/8DPBOjSiiWs3ev8m6Lff6cAKti1FV9zBXAYckyP9TpED5uJAqIFhz8cx1tIrsSJIzmqdjR+rHoGGrsvWYaafFTkIzQtRD/KiTxBBagJ7n6FiZtXBPPdfc4XPC44n9eVqFGDjOZa1FdDdY7Jr6KkEViNZK+2aVI6vdhM0DTB1TWXU0SGIkTU1V9PxemZtf3wqTmfzq5WBLu+s86wZ0Tgg3SFXTDVEhAGlQyDne1LNoBzQzqUtHHSIRSUZpX9akAOrg1URO4tPC5kAuTw9/Bzx2+GI0sfnAr4TldC/cC7+JwwDjld3HZX2k4fmSXarfPlAOEThUVoA9k1iCYbRWp4xSGvDcDkapHkBKUeSCAWr7LjHscKnsv5RlHyhdmZdH5WBmNd7zAKqO6TQuMdn/OdZOb/mLnSUbb8A4JI6FMvp4Qnk8I+uvP2tCXpOv6BXISKy6ELZ2P1ppbBF5vOem5sltigIJm/0WtFHSU4XW4uA76pWoO89QBP2+6T2ga5TlVO/Zs4nWaKsO7ONQqj6FU6xd+U3n3ZtPMOaApksdHkZCe44Yi0c0ivZ+zAfkfe5o9CYONjQB0epv6NTA4xe6379dnUV6IkkGaApfgTWP86FFAlTnQKcAIX2Eqnit0Y1jiRtwDwgCiVN4dJL6pGOFDR+BVUEG76uFSB+6UIsyyr+utCbLKhAqcJrrbzntUUn73cE297LICJ9qgBEi4h/FstNJGMltDfS0XI0oeWtI51L0+j5b7KMf7oVhGKak4r7akFI+PKA9jZYP3Eq2vGgYTpceqdgulc0YEugBpitH3ojaXVFCiiWN3ykh7HLwfbjQcZJHbfbzZWjxhEOi1eAYradai4HHSbwqpqMkIKipx/y32cOgYaqfc4Xn+c6At8SORHhfNeVjFPb24jOfrK7Rn51To5KzH6IIXydTJ97TboL1X0CEuyQ6wH6rYuVx3a3OOn4PaYykZSxyie/KFfSbxO/QJfBwcZBNljINUPF81DtyFmMS/pPUEKU1pZ0MPQB+aFcDRDyK5uQ+zrEDXZSAYrLI1y33woRvaIbVZ6Ei+sEUBVCk7rmtFW9FX5xtIr9Z+q7vIkf9c1tt50cYNYobWJ/6vs/fUB31Ios9V5XfMH4dlflbYcYnzvKiYuARoYsPMegdWnSpZyjOq27MSXgwJbmhwTxQj6UzUwMvrn0oxcAeGe0S4Hr7X7bPKVd9xZXQ5aHczzQf7jH9085YhhDDnNX5kds7Xki7ofgf4Y74V+xM6bCuMHTMu1qyG/Vts7cMtb30zD0yjX9qlMUl+2JAH+8/P2lRm+Go88wuFpYvnZS+nawzwu5MkfHmFkULg3xc40ex3USa6SPy/lciwFj0qX8M2nV4+K0Q2ekF16dOkYUNEeueXVhHVyUWRdI+WLS4XXMAmELjK4Wk7QzkTlsNTjpRrnKE5x1cMqz4aIHDv/S/4sxZ9vxThHZR4prH2ytuyQCoYqIfW86+1ZXVdZ9DO37HWwnfSeJ98oxTRsELimYYsgj7uARODpXjxyQR06U6OAh3U2uCiKNmSOyFYLxgQ7tZjlFGTL0XhGW711Fe0j6zbOFgzPB2uttsOg01M7uWl5M5QqT7+1eqfk7ZuhQr3TDjz0DOrI/sJVfQEUYqirF0a2CDNz2oBeaKbdPN02a5c67V5ub73XyNNhiXu26Z7Wj7YnpPu81FU5F0EUEz59N1sm+kqQdetJqP0ul28vIynU2KFgS93LZXg9FqZl0gxX78AI6jbjDdB9dPLuOgmf3ZWRkgTyf8yPsYg0u5LWH+ne0bX3I2K9j2zXRHN0k75vXNwGLzYn2H9n/HDjl8ebJSaWvu3RMHtT2ruxONJ6cgGCmMhxfH11IKxzW42/BtZTRtxtYtmTMnN9P1KP6VC/Xcc5zYw1x7nC5AJaelEb+3WnXmrgtbutDVyysJ9ovnAmFPD2hD0yF33PM6N46b3p2TJ5EawTEUsIQ44zX15DhmmzMKLg5czjRIBNHTLX1lN38aMJY/ZBUfa4ngJWtm8HE7QLCr+QfB1KPHh4DCIevdcy6DAodqOkrXthRo7gBTwuZ1gKjZ4ziEqbbBznIoNlt/gDpFeaycqqRRRuyhJw31bZoQXj5tCIRTUQGMAC26oRBts4TAtAmG07VmZLzxhbSY/zRH1GnxkWjiJB5ulqNz0EWM1DXmZm2LL98P9mW1nUU3B78TsHlWCve+LhxvXxcXdKsyGH+lD+a+qMTRrJGPXLSRU+1c8ajRx2t4+pM8LqJLsBR/rD6FzFLqEd2zmQj6/QM1s2SVdpLO2lzu27j5Ad1B+T65ycCATWiSFeO91UWVu88+gXw+oa03yqrMzEZH5of/b/7qcIQV0XTTq61V8ehPj7kPSz0+jTfNiOzcR0b5NfCBd/1BkcdN6fSbQq5H7YtoC9SyORtS0cx5EPGmGFNpPA+qFKkGSHlu4ROg27KGBvS9C8U6cv/EIf73G9CbP9MKKftCQVROa4Lhgu+LuIBlcqHXO737+dymJ6c3UuhgFRl57umhlNjuHesCl5teH3/Whmx9L6g5zEUG566SICR4Aw7/9z8RuDBSsQ3nWraZAQ/sjb1/fcR9X/BRhB+UlMIWuJ9D/nnf9Mew72QF9SvmiMWz329eI7+Grm6dpQY/fGhmJl3z/OIOLHVTSSIr5QEiwD/QT6x0LgRdtHou5ZXEDts0GB65HXkvZb+mEshdjpFSkTtV8iDWm2jv0VqqZt3z4NJlm19YyQpm3S51A0nfWk212bYPcJyuouCg60ResBm3hoMAtt4KjacKQy4Q2Nk+hqDbcRj4S0EOhHwo5s2o5HHiMf6TgSjhzs7Y0ePh3t/FPt4xJAc8j1Kw/1utJ4jzrbeRNwo3Ue+G9zmbyUmxvfmYQLsYXUfCQWO9vT4T+5tSjs3693ZAtTNIgcDQeeQDbo2ErGMb0RDxqbalKsqu1M7MPD5Nx8RJctlmNP6MbH2vkW8BaqQ95Dtld9h50sJdrE4aOGvVM5aXEeQZstS94rUUPL3F1IwNBQa2BAqH9o21HXDkJUvx14CbA1uVULjiqvOktBpQhL9TZstY+PC05y805vnXceK/phN/nGw6NC2k29/7P5mxzP53DYbk6Xo2TeJ/UpFYz++e9Vq6fe1KabVhNnBFMu+vjGSkm9zdQSO7Y21pBWb2+nqf00fadnQaCPpQQreFvBDE4OkwzFAmscDQWhygAI9rNKW86W284xxx1j9x+Ph412d4WO0lH4Jmn+WCdOFothmEt4aDMHXmhsTsR9mzoYL/T7/NDH4dZAIFq139jWrpjtkmpjFool3KOgPiHcZN4EgLtT13BS44dBnA4+xlpl3iQ8ekuQpGDpdTlcd8vmT2cvqO9LkO9lp5ueJUU1lItSSztXOAQe0/cCYGg/fhK7qqyCM7gXoQucC4J8v1B0XNBo14Q45fYl44fR3F2o0uKyu01PejaneHSlAFmy8aV1xP1PozniiDodOKwuNj/IjawJhTKf1ZqVY555ZeVoYptjEoRTi1KvHQbZtFnkpPkgqPJcHBAj7OytHX4cWCgNcMQ3Fnd/Xke4sFK+N1xu6e3t4H3A/s3n/LrZ71Da/P/1WRWzu2PmDU+/pEoGLqVwIifp0CSdb49MFdd7nv62wZiDW19Hfd57575w0HgW7VXDDvzmpwp2fVHMh/Zc778MyS8zOpCzNLLs44X5lLnd9afGEr4H3OFGxsfsu0atp0/cdwaPn4fz8nQqu3Az62dHvqqxDnq1D0awEMGEzH+1+7QHx+bM/lzuKmv++/3KWw8M49dudjDQeatAeC/0wqtHdIdQGDLR5rXrnXmRfyUC+6H4JtVuRl5AXah5hMHth5egpYsLmB50+XPXd6EJ9zYbPlj88OP3awFD0IdrGyB+L+4+1dweMHmlr9myFH+yF3VkVGxRb3iA2aDPlNW0dJH5xVmPqbHH3em3cSxxWfExwRELDQDq2xw8Y4w36rBOfyXabX3P/3mQY69NH+FOviQoRhd1pOPoTcsx++2PIh2N4grL36Jx2m1yESHX0V2eeJNkVC4Z9Xx8k/Wc4oZbVGyMDi+6ssx8pG9/C4uNLqNciKsR+iatA/+aKOo1HDK5LjUl2eSCwc/7+vph0huxny2UNL7nz+i3qwbErPqePIhFAFXPNNNTMIm7AUohpxODTDrbAVSRiVPVRhnmS7NXhTFEtiIlTK8+sjnk5S/Ec+VYq2M8BeQCTQNUc22ecZ8qggZcGQFKwecjLakQzsQilfWyTsa6WoQFskFMiAMhbWiZhGado01GlFtWGhjhmyTeNGrQyXcgN6PTdEyGRq0jBt22pgQkLwxMhufsqKoa2wRp6Fqdrvexcz/62e9l/8qRpF+TLRsK8VVLCQbh3U42Sg3k4D1Bji6NGdEJz27jiMDbCgloPy3mb9fyL37jq3AVfQQpHHoGugaI4YC0UieoET54rm36+4/32w2K1z6va6tb4UNSyyBzGPOBym4T7YhrcZNfus9Zh18DBM0kZF20KRaKdDRgqwNPhhOIZhDO1Z2dJvTkwsltwtsJx7EFEhoPxKZNRbjFInKInF4fS6u25gpRHMmobUA7RDO9QGYUQzugTavMn+RdeWDZ0V9kAmFAik7JQ/beVWwMzXH45VDt0erZwSCmhl8ehMO4wwzWFbC/DonLp/3G0u8w+GgH1lxYA5sdzLtS7GZ7LCgPkIh/qbXUD50V1f5ODXiGeTw0abFdBGuUC7xYvPzj569WSBW6eSSUjBTzIDG20Rvy1DkFas6oBNtpjevRZbouvNmO1I66TzJis8eoX7eYI6lr0PNY1StHmo12qntGwaoqk+vhe1W5V2OT+kD0azT+VYNqj3OyQl7zphVj/12mtTSbumCzWOUgMYnrFqfhCjGc2gmFWKy3mnsXqeH5dKJdrH9+t/hMeX4iEr0opoRxwO7XAGRi0pozoiWm+wNvfRSWtK4hmGJZeQPc7xqMj15dJG31PMC/aRqyTLKG+zAwz5w5kXX0Q+OD8V0gxD5t6lF74tQCQwf+eMX72+sHj7MihiNZRN0PDSRZQjDP5ixXv8+U66GVcYVGfZ5atFrpXoMtSmtCQoryfjvAaj295UyLy15em3nKuw5TittqZtwFBQorwN+fAnfovTZoKDjM2EGWoPcNl6Codhv9v3A/NLx4bRNiQl1ni1igbaJVSk0LRcHdAZDOF+Oago8FEU+Zmz6mrhWfnKJyeQG5G1jyMuBPzMktM8oU3Wwjh021UNpFDgUBSPTmXhMdbo1ZNMkBuE/fn/v1dWc7fMTfzJp/9xbcsRxOZMiDv8rTmBv7/n4NhM4dlMCMYfnhu54HrjlQHoDrWE6wTR2b2RNhn8Hv/SK06khLk+31d2LWavmjW6Eck6m3r7xYPE1cBmwAPzpTe4a+2Y1xf16Gu5BXFyNo3rP2/x0mmO84r7tx6F9fzDOnfz3NddEbHqwvrCMN5VvFzTm7NOnEnJ0EkXPhEDRf1v35Y9xAyurJ1DJIjy7ML5C0Hz5ZTQwFmF4wvv3AW/cyrKKX4FheqN6j2FOTvrJVKM/8wc8rxlJ+VR3EUf8pinbLGib8NQTvQxLyyUz3auLn5DSRDFg4PM4Nz3ikFRxhY3DFr9yhezQ3f/u8k7AyHV8EtPS/l43DSNrdTVUTVarVSPTvON5ajck6hvPS7njl+1hCOZxb7x26sFyVYOz5v3PNgHtXulDKQwPgeXYP4AhvsCGOoLY0qBsEHKE/A10gY9oFi+jXHsZFcXOrsp6vNtjGKzXd3YiY1xL270EeLJeEw04UNMJh8qGo/Fxdt8OHh/I3LeqgpyP6E/9XEtmu/084CHdQSnr/Vn6v0CE4nCVpe9APOzEuOjXemRjriCkw72TE+2e0X7CMBlEZ1KSzof9xfaAk4CoXETbGegMBbQIRaNnjCbjD4sHw40maPtCivcIlZ7tQox7RAqvMagvCGgM+gjWTmYenjFvgrpocPvEaWm7JfueVDH6tjUvygSLIa8qBEKOgOBoB+R4dzztppN6wn7xdVrOVVOoc7aqtW12+269nYN0LI2TZ27Nwfdngt6oyPZ4mjwegLShMK3zsBtO41ohKNCUjpNG4YaM10aFEc8PpJi/CQWdRFygd3GB7OLbh+nxu+mjhGfGJyDba9rX8nvAbUsqlulj+kapQFGIVspIUV8WqrR+jINCJJu0PrUDXyKFEvr5U6FNNCo08e6VXac9NIQ5CFtNg8JQV6aiFlssFpLW80QZdWq7TBYwzK3NBibC4ggi6YRg+hHPrmi3wknrzdiEY7K0qLTZCyYMd2tITZvffDUqOH4oN/ThIZpUiYgSb7U6vbacMYHeHKzKu4jm0w+s4qU6u2IAfI7Cqz+wtTkUDY1km1SCTyoxaNxN1q0bERQvI8AQhaTa7Ke6OqyzuaijGs0ap0N0b6kk7m4E9c4CP62WIw37kC1Wgdqbize/8vkwIGcNVh/4iaPIJ9+luE++y309AoWcY4AdiwT3HatM1PjF5hMqAnC7flYqCCxYbQt0dcRV7DTnp4dk2mvaAcBVCy0TWlK5+MhFkG7rCYcN8EYY3BjTrXZotFbzBq1A7sGDjUZoikFbIqLVV6tQkCTQimidctFAZ1BE0nLwaaHV+yrrjr03vPEv17vl755IGOlc/2LIuEii8PaqGecgYDTbxLB3DscazZ1EMZFK9f6q+zCRnNCq2632zXtrRqgZeUmHrwnZzo5EHIF+7PF0fAGBJK7PROyqRb1ceRQk66xkz7TpkFwE93BbgtYzf5Wrh1Z/jOL7hizjd5D7SDmDV339BkLjwMRi2hXactBRAFKIVWKURH3tKnal2yA4URD41guhYkliHRiirCJNpZV4TjsWEWTFivdgaYtMb11FWbVaDEJjalkGZoa9M35RPi0TBxR829ik8v6HfD4Tj3mY8tMTTrVqaM+ndWgY5s66Y73+B1NkGuczROGjVSRSInaVB53kiGT0yxfFEVUBprJh0Os5MaR1qaB03uY54EtDg3V+HkdoiueIID+ut1CM5zCSJxMQbBwN6AymQygdvGfP9jwgb817YKkHtB2uWiZv2iZ67I8Nfpi0W+mot8Knn8S99dlbSX9kfqTuTpV6rXC7TGqEGWusSCJPhWJtkq0Pr307S99X74rC71u4sIrcIZvYJ55zTyfvy6iVJXoe8qPH2UrA1oYSUF3M11EsE8KXtH5dsG+Szw4cWrl+lanISfKiQ2G3SbODbEAKuBAyxz2wY+u47f91YQ0ld56HgcuLHlZgGkR6L8+PzcGspeL/vYX/d28Edvx60l/F8xtpK4kP2j8+BbFdhO9EZkWN7oa133h/fwtSYJ1TT3GG9AEdPLrbqf6MgZsYpUtKZfXtaxkTVn5GsDs4u/9p6E/VVJYtri0fPHqMo4YUnlANto5VW/q7GTEPYJXnlFXSw+MNOoZ7MNcGJHPUb7jsqSjFew1XPZSdm0Dm2sGO1RTZ+6Z1vb7p9Zf3Hv64j3A+TkVpmTV18gdCEBXOLyTUYT+MACru9LR5rcH+hLvpGJ0Kpa6khvLXElEwcbvpTfZwo5Gi2A1Plo9c5AnlEJSIe9g9UxuNWYRNPohN0+0r3LbC3VQPM7GC+1z3CfiuSFww9dqWFCCbX95h6kSHBaorwm/MlXJ3yvUEQbQmTfO4Hj916/naq5VGxgXXIfjgh3BCYuWTvlTz/T1Z55O+MHGX2UD01Jgwopjn+095EJuo1VQgs9Ur3uYeN8u8fD1zD0lmLXZWOpCZfuJ47V79tQeP9G8CxQe/a9qi6AUu/3lZ54sxS3gBlxUvn27nBuQ4tYkDud+fXzh9j8ckNw1xV9xoeHlSApg/7yxOp6rAPn9E2dqq3vTmbyDdoDz1tMS2G3dDHe/FJD8pnRCIV+09NnYkiXrzy1dJFecDg22f1HeKIY03l388uppHaqsLi1b4pGroFL54tIXPCQXkCWQbyH/h72bNXCHJ3ZLq8+wu6drxhBJ3WL3Tga1NSktZRcK17z4+rOKfZRUZPXGKcWakMZKcgQGwsq6r6LdiS4Zf7+k9AH9SruAtHaOGVz0JkU0Kh/DveS6HUiLurP0yrUnx6oTH5V/2eColVOi8s9NpnolBXrH/7Ngj6pSIsXcvEalhyNDZcZYNLFmN7XcYZGIIJlYdK94Zf6NmZkjt7EcQyooATM9I00r7l9nF/UIyITLZ24WWr21OYeTrF6nT3gt2TqQ3vLsqDbYIAto9bJQSK7f7LYuv3Y5yL+rRPUwuzb7ZkvZ9ZDTYEm4f+e4WLi2tkNlTJPxrl89rc7851W5LRX56mNagTtNSBoLl6gucgxiwcnFjm3a1lbtNodDsWGv58jjaDaaU0aiihyKMmbM9VDeGxvURzSKJAQx5p/IdUTSz8JkKdTQiHoSDqenGdGgxhYZC0/4fP47Y+6eQ1ba1BjsL216PynGi0ol8tKypUbus/yNvJyUz2ZzpJ0T4IFMxBI5J9XINPXStpbeMLsnnG6zeIqybqzNWciAxx7lwRw2zOWyIZjN4/9cD3G59fAv4xwVl6Pk8JQcrgr4tsxgM2ChJSlV+7VaedCvUCNSu0jkVLjWZbZwmIIp64izoD7OWHUGO4zMWh5EXTRspHHLVYhA6paCX96fhCcvbYG3iP/28xls1dlJy+TsFssWw984K9Msa2+jlyWTLpe+SdzJnkYLlBURnnP+2bAOsrbaNFuDQe3WtM0CR3Wz/gdx96Qyv2+R9eNX96ObyXge71qgISRYXZJdn/l/t1CvDLXK7LaMTB8KM4e8JovdgenXBp+OcsSSYZN7wQHiWyVyDAFF2A/bU5dCnJMR/fpixHh/IgCR3jyP3HX2APLcv8CeBBnIhoLBbvIT4IeS68QvGYGPe+Kp5Zv+2jt0W8u6VdcfBu1Y+JOZ09jp784i+xCgZ2jMobui0X9jRZX+a/+7b35x5x+y5tXUEzxDp7y9z7z2s7yTaN9R1r6F2HuzA1zR0ptiA5ej/R5R60rKKxInoWX1bO37XrWtpKwyMfU9CL6AZn6zf3SGds/xga9szhN3lCUguWKX2SxizBeKbWowjnvMSznOV1rNJiXM58sgMySzRPXCu3nRixRSIjvwlBbIpEDyfeUWcEcbG+JynhbjML9y9O5Q3Mx1/epfK3xfJYBra/mL8C3ooWfnHM/MeVk1z7DfNmIzZ9cqsHFxInxNFZtWseGq6jq/zvKeGZYn7EZ1NBY2QRzLGdkcZ3DOV6w9u6AtHdZ1FrBmTqOn884iDyOAYtbKq3dti3773LdN+q3R/Zi3d5ZLy8voUZeYy8rNq6kneIZOFS4+86qPo+dOYmRH2cgW4uIn9VeXtZfnyPk5O6vuVY7bZOYwr9bVf8pmzCaO+1NO2XU4lisvb8Pxjr/07/wlFajLRF/fLFr7YAPuoyjMK5NjHpoifL+UGyViYUVlkViy6LXGd1y7i1e/iiC5+wHYnCIxEk/B0AO7gX7H5XnqqTwUm18A5g8fPP1kX+WX4PjukfnLT+Y9haEL5ucB+U8DivYFiTli9wMwlEo8FVgKNj8AwohNte+Ft40XuHQnqu4ZmPh17OEPqjPqr5g6g2tDJJZi1w3DB4xJqt+3PgVq+uLROKwFoH+MB29ih/av690PtmFU73kq2IBZlPubB/evsaDrF/nrFNBj1+/3P7fbb55itoPnsLeGnd904D2L1MYR4HJYJGuQykQWuRAnOeBEg+QdsegdieSSSHzpcun7pSXkl71fgmUChKmeFVy1fOWFNTrOk/q1a27646MVq357feqfqgT6LbqwDkCIUyZ3NvHv+H3tk8FWAHEfzex3vwsOcP8V5b8nmhVMaQlYuizTV5rU5bM2VPEhIZh+VXB3rQh3dB1+pLJu2YLFwku/NwvBwL9PonMpRHwh4FNzGUe8durNQv7e39f+XD1U9i/IzYWfs29L/6Im9yW4huMpEQigVk8b4spv5JRvZNt+0ieI9XVc8E0cuthuC/DnJl7KQzObAdvX859vJO5iGxVgqNca8NXoNdBAUExiGx6X4jwi20/6BOv8elp9Hf86E4tDT6ixrxtJfxbnW+UDodGJ3eQqXN/Hy6CM6436/D2ST+aTPpET/XqEvi6nOVO+9EFl+0f50ruJik9puBPfWj7f4AxAUKGf+u/QFeGM7AqY7W+a2Z7G1eR/yCe54BNk+zoe+AYKfBPxTTNnCfD1aJyR8NAURAph7pQhSU0hHtt2eRnCixSpIThFytSmOWaQkj3TRg75JBt9gmO+jtO+gfO+iV0X2xUjSE19EvVnvRfhkyp8QnWjczprfD2lPskCn2BLo2MnG3092b6RSU09taCmgyOwm065iP0Oljad6LE/360rEGpG0+068pUAWFPvONFthr70pz+NcyYxBTBEGRJHLohDFrAnrclYmza2wUuOlK0cG/QUUUvOSGhQ0Zid/mYhFCGIiObb3ULRQBBrRuGZS59V6q+UXONCzjjeLOmIJZxupco00M3mGoC41nQs2eYxKSmAF2NlrVc2l6u2Q7v5ufkBKEg/3RCWQMqu5uo0O1tGs+QasZPar6fY6Xa3ZtqkON3OCwLy+sYtkIjnW8gAwYhcHq/VDyen/1048lq/gnhUe7vuKZTFXOkbME+Zj/azA7umO6NGvoUXX8zLzFL5DJFJ5Y36/GF1ZasGWSpsayRtmJRMtdn+ot9KqW3eJxn0XMGwRi5NjtiR0+3GGfblTBvZ5kE6nX5XJ40/iY0ue8vZ8eSM/6Oqti26ljmcPnY9fKfKWpn9fHlTz3XIwLMdkiNXcMQunG5PznCAyrRF92WA6/RLcWUa8OJHm/kkp3yCpD0d6YN50HF2SXLkKI5YwOqWcI3Tn6Yypm6qiOHSWsfsL7ehkzRxml1sUWbnD2b/2q4vBL+TLNdZwE867pbilIckSG9r+Rjl8WRLVcR2dxBtd5RaSjHYjs15p6LsjRMhWb5/PK5jK3/u4Groax0zglt2Vr/s2jGmpEzmJtsjOeMGs6Qj9uF0B6pMO3SY+EW+qYlj8mVi1p5QlF3GjhzDEYtY3bJM9m0hmlQdO7WUzVSU3RrMTs8GeNlMaFnIZt7yWeEDp4HCPsw5Cq6u3wRcq7yS+32hg0y9MRfVHHsOts4u9YIF2mNe9rCxq+pc0pI8bJ/fm+/3jYtG/X+ieB0kV2TNTVyzFyhvNheHuc4YD1eIB/uG61zx+SAB6v9vSMu2kJv4eYLDc9brp/ZIWSdwe6gQsVKPDj0GSIw00kQzJtpop6Nmf0zpBLb8qyf75b3p/0N2fOzX7v79zy83712rVUOxXP/fr5zb7+SPlQbAuqdLUvqCb48BAKT8gdkg3kt5p/UScynmctZxNrROIyrJKPdFOBMkEziN3DGRSCA+agF5oc3RuhqQ5Shjaae68qaY97gmN1KDuWV2KU/glO5camgdajFnoBIK8DpSudP8GhAxdTDtzP1ZTnpL/Tdxg0wPyJM1UIkAmN9CQICWkzQCuU2gRhJJieHJJF8EBJZo+4DbVvhygCTUePPoGwnRW8eNRuvNqKwZwmh7DVsjRyW0U1Kx2o5voATFCJEwGEuW88dtlE8EUtVdDzZL0cSZEEcdOsoxWQdcYCpTVT5go2GjoNGziPXIWDRiJKy1ZKJgpcHZJ3plHyfM0qmaMaUqUlXDNKElwwP3j4bo2uppgTRr7etBPy7R2wjk6GsACJuek14xpSIeyblZqRoYQjVIgw6nz5a5OILtWNxZyw7OAHihph04tjs/IbQcNUQmltTcrPJ5lxmkeqOaq+B/JFGiZVPJtEMtLhVyEyxqRWawH3AFGZOiAtnUD8QwYlvqxqEzRHF0yERqZJ6Uh/hLHua5MG1Zuot4xbgoCsB1n49PQSA0xjOgjblb7krFWj+wNG5kRgb9qYEa0UpIs1YeAA3tk+ggBfFTCqG8lh4yb9PfkdfiIfoCPwk2UzntbISOPny0aLz0ZirXRAZyl/GkOgOjU+6l3zPGmscDhtGwEThjI2XRCZGx3hRtXtuy5AazV/sWrkGatY5lkX8cTh8m4C2RiaRona4edCsm7RT2aJ8wAODdOvmKjX4DQGxLBnBPMp1ByURpVjT3O0YBt2egc0zZXxTWbWG0Cyu/YjrZUozoaDI9Swf2d/48kD/KzLWmbrS7rMB0yxNS/WlYfIR3sH9Fx2eMpO5uHzKxbx0b3zB1j0SJzShpTjW770sXUnB2tmr63RDzdDkzBpeHPgR7Dr8ntDoZyVyRCiKXp4K477iXQjNrkYuZM0ZcLDV5Q2hR4s4Pzse3FWVe/6zvhieWEwXKiZ8k+lf4eNsNzdf+/cuqAFvdt+a/+d+f++jXsaF9f83n892Z/wG4vB+b0a/Vi0YY/k7H8TcA/PDh7ysAgF/8Nh7nJ002kvQGQAUGAALpi5kGoFkz8QJeFAT9FeLfI5nIeQ0napyTRuvzL/5jlCS+I7IOhCtuFRD+2H+jFO8RaYAhiKeIPOaJ6S2lFkcoOonAw/dbhmBOEelTniSDBekWm43pM3WWoyxdvOtmmshnOisow8fdjICeixancMIn/llCvqyv4XTByL/Ocx8uM4vlx+rBIGvVCJJYs0ifxODqDJoaT9Z31nraXmaXRlnl/uXVn2EsY7KdGGxSbSa9XFbhsTROAiIOs7kcMYRgGHsdbgnKW0OnS7JM1wcRgIkAfzIDIZ58ep/MN+xPb3Omjap60Gomvm7EhMzpm1VxcVJXAaRH7G4Bf0IJeKi7hnceUD0nKAsagUH152ntdVwbk5p9S45l+MwPje3LXgS8+TeklotMXg+fqu/wTceUxTsX6Tm+GO+7rdkave5pbGlcC2NjuKERVu2n7Srf1CO1ufXLhm3OjScrVf3UOQh3mR6PF+2434j0HILXuosGkHQQ5exF2TZsZy0OY0I+wc0Mm0DcvRLLwRBNkmVJBKmmfgADDDFQGIEAgjLCPAsqIe2DwV8BCJwKKM2u61rGP/tHjYJtv3fSimi7GZTzIm5dQEVz+ldpBZHaxlzimw8AZFO4VF5pdlVzLxxSlS3+520n7UtppMq7/0PI2GDOMG92B/iWBUrIodJzt42lDn2mtpPEHgL01Hbd1L5hJMyEHAZH92Ym+szECmM+RnHWm728wtrEmEYeH/L5Ea95Brd+wG1kOVfjUuPn+CZy3sdlBtW3rIe+CMRurJ62bN9agWoZmJQyQFSceZbjeGyj1DQGGYYXBpSK6lNsbkX138eGmXXz+b/2z1+wBFtvXGr0IHm6x5QkHAzuxwyceBL7IMYi73/Tev/sEODf+Uc+U13z456L/EJzehwcVDAA+PR1P5URttfuMga7OFzGmXhZyhQ8rpVlKqPOG2UainNPmQ7nHCwzcDpjZRYehyqb4XI4ZXMd4qoyG98u3c+KtAceBAGM7SChKBgvYyCqk3AEflACCNRAAFqw0htypUHQgzdgBESZCS6yyyxwcrxsBkz2ls3BjE0D7MgayIKCFWUOHJFlLnSCyjx4VGU+Eg5lAWaISEgBc/cimAD76NEloRtpUEKnrBYOPfrR2ckjrauQtbhuKekDA+dLXcGCzlSfXYFGioYCCvjsrIw2g1FWyqCBdVIxrV+3xJWrMckQuN/6JbfIleMx7NKLAdnIhorzK4Wjhx59xtGnHj3w6GFHn+l28MgizOi04QZjp5yLJdw81BHVKPXsYgCJAe4PUsYSU+6REFScZlBvczqePEuxRb+s3iqSqMnqJGk+OkMqGIbi1SZrQDBFWsUN4Wi1IxLh65piMhvZsKusWlPgmiEmHRgSZTZYr67P9I4B1RDpyNHZrB623jyWQRkJqP6RGRCzxDDLeVoJSfTybbIQ5F2NtDDXKx6hux3Q4ZGvJCHbagiAHpMJpSyXWCagrIFWCCUW7aDc7AutBCpKteRvQpK0yk9SBtwDcv2uWZefeK8QBkq7EQsbKBNyJ10bIspeX+1oK2nlHmGaAZHRePDX71/Jz4IB9ZrbEWr6e5ogTn75ofQg+3e3YrDSm1avHGbcViclWyUlVxT3bh14CglFj3a/JZ9giC+ScHW0uZwjeiWjFockqT6/dERM51tdIfGQDD7Nh/FZh88v33H8AfLvALNVhCEcyix1dxREhWXuEceZiz/+iuoacPW2IYgOcstjQbnKmFAVC5nBUG76MkdsGNYSULSUajVq9auL63LcebQCT8jWGTp4gcuIMlacq6T12kovQ2aanEUk3HS4j3yMgHDdgK+cossAEuw4I+evEz+6nNFb5Qoe7DT+RsFsJhMpZjSV93lQnCdjaqAHTvYDUahUNViZTeH5xqipP0heENl8+unQqb2AQbp1OWwyzD8BnFkI3BfNNQ+m6S1Cv4Gi9BUzDsnm9xbZjL0ElFdtNmykJEO1mDINXSuOMjjxWTfhQyFcEK0eRuvGLQc1q40hdd4IR+xxv3DfiOBDlL0H8TfIx363he1mNewIQRsbZbMD9pVzzHWuJyQ8sJq/BeaJ+qoDFHWQBU3QC6LpB/VsFjfkmqfuynwxxdSB13DWXN+dS7xPirJRsJ31IYfPTDo4m37MzXHw+cRwWWDDVhYKSRwkeuEYc/wPj8PgjCu3wkqrrLbGWuuQEZawHjrRabBBUqP0NsHx0CMTMRTcArwsLtTMZDzDlPPtiKHTvPRqKD3FPPkyZM7+t0WFabc99vrGt77zPY4YHHfUKSeddsiivuKwIX7kiEt98jNsPvuigIw9O0vACijti1/95nd/+NNf/t8+/7PfAX/7x0G/M6C04TCdlsvt8do+v7iEJEWKGjGYSdeTSO2amBg1atE2uUbpjKoR0JhCyVmJXxuw6mESCA6rwhKcOlrdFBEmhPIINAgOBAcNEggcASR7nIbMHgORs7ugxLvvECJvGT/+qW38YPmh04Uda+hndMrSoP/sy4h+gr+6zkkXMEwfxigdIm69jq7ywChLz8XTHjjysQdM7aZPz9AGszFIi4Lb+6Ty/f8O5jZ0rdIZLLJi7uvCU2cR1eSi8Lxgr9UDq9lcffV9KLt+w8mDqyuT0S85jO+0WwGO0zYe2Cg9sHWyRdvmyOa36soqgDcjTXaDfJ4aGWVBTpnFdFOv5S5LJ3sH8lyQKBeaw9SHzJFT5iYbk41A9tlF5mKeehONLNsCeqsZKjZFhemtRxdlqb+hqICEOBQ1BreVBq0SFa0ihLGQOdmoSOiOV1pM5rguLyB4qkrTsu7Ka3AfHf1jGnOA29TJCGIFp5GkadPGlEYVmkmvT+YWuhZVVkC4nmc+7T0wGzIH6QyfHWpIJxFc2dV1TroCPoM3rzYT0kyhiGSQEdwAIbwzh6hZnXQBMlMqUpGyTCbpSUuSTNKzZJbM0/IsOBvJQq80TcosVg/YKpPl63KAFd5t2xedqCtdrZeGIFGuNO+pb7OKhpdBGS55ySLrJNLMbL4mT1YCl0SBs1J/s8aEBNRnkDS1UxGAQshucATFQklvAFSitwKgQo6LXLd8sYi5ZgHZbYcsskg0y3YMCiEdYA/CApoDpz+Rqc5QGyCI+Yef2pHdQBr58eVUObt2u4/NfCx9WnJiq/DBZa4ZgdV8+miLElEss0QAgxOeFyA4nRE9DK5wNayxBZkdhrvHYrOVIUuBqWMyAg6NyXolZ9zWHVN/SSwfBTuXhkf2b4c6J/aSaYSEXzlGvnW48fbR5DFpVP+lYh723sl3wt0wyHOvTBDDbMUnM8vpAtyFsf3HfbFDmG6Gmn9mvTrXtWCVywXzCTMaF3hRYtLdKuq67Jb9eszgLRDYYkSIETOrM8QG1HpsYdzAjCAl0Y9UgcUrd019pTmu56fLzU/n+m7x7DdhlhL2kWEpvwNLydTIMjhdviKgACU+djg0mjufisCWfzPqTEVumjMixTv1bTONGfEFaEUPa1jLNTOVm8DCaEP87JzSS2pX+Q17txkR5yL58LcVCYDGUXuRrWVRMEUNbyvhyJlU5JLH+C6niwHJzMhW2YgmRsCG9FG2VomhTZAQiVLnp/so8w1dLFETUxcHezGRt4YwVOGOcjnEWd8fYzNSRXRV0pF06pQ0hDdoR/XMNv+6tklm7x5lnYsoOHSudknkqev3XPT7yLUwuZHaEaRcFVM4q32c4NJWI4fb7hWGFOq1ZSygFHRJCxFXQTpGmDpVpx/SyU/8c1GGHwAAAAA=";

const CSS = `
@font-face { font-family: 'FQ Instrument Sans'; src: url("${INSTRUMENT_SANS_400}") format('woff2'); font-weight: 400; font-style: normal; font-display: swap; }

.fq {
  color-scheme: light;
  --tui-desk: #d8d7d2;
  --tui-face: #e6e6e2;
  --tui-face-hi: #f2f2ef;
  --tui-face-lo: #cbccc8;
  --tui-well: #d3d4d0;
  --tui-skirt: #a4a5a1;
  --tui-ink: #1b1c1e;
  --tui-ink-2: #4b4d51;
  --tui-rule: rgb(27 28 30 / 0.16);
  --tui-cap: #1e1f21;
  --tui-cap-hi: #2d2e31;
  --tui-cap-skirt: #070708;
  --tui-cap-ink: #efede8;
  --tui-cap-hl: rgb(255 255 255 / 0.14);
  --tui-hl: rgb(255 255 255 / 0.9);
  --tui-sh: 24 25 28;
  --tui-sh-a: 0.24;
  --tui-grain: 0.5;
  --tui-focus: #1b1c1e;
  --tui-ease: cubic-bezier(0.2, 0.7, 0.2, 1);
  --tui-well-fill: linear-gradient(to bottom, color-mix(in oklab, var(--tui-well) 86%, rgb(var(--tui-sh))), var(--tui-well) 55%);
  --tui-raised:
    inset 0 1px 0 var(--tui-hl),
    0 0 0 1px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 0.35)),
    0 1px 1.5px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 1.2)),
    0 5px 12px -5px rgb(var(--tui-sh) / var(--tui-sh-a));
  --tui-inset:
    inset 0 3px 3px -2px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 2.6)),
    inset 0 9px 12px -9px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 1.8)),
    inset 0 0 0 1px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 0.45)),
    inset 0 -1px 0 color-mix(in oklab, var(--tui-hl) 60%, transparent),
    0 1px 0 var(--tui-hl),
    0 -1px 0 rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 0.35));
  --tui-pressed:
    inset 0 5px 5px -4px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 3)),
    inset 4px 0 4px -4px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 1.4)),
    inset -4px 0 4px -4px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 1.4)),
    0 -1px 0 rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 1.3)),
    0 1px 0 var(--tui-hl);
  --tui-noise: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='1.1' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.5 0 0 0 0 0.5 0 0 0 0 0.5 0 0 0 0.28 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");

  --fq-paper: #f3f0e7;
  --fq-type: #26251f;
  --fq-type-2: #5d5b53;
  --fq-rule: rgb(38 37 31 / 0.13);
  --fq-rule-2: rgb(38 37 31 / 0.34);
  --fq-fibre: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='p'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.55' numOctaves='3' seed='9' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 .45 0 0 0 0 .42 0 0 0 0 .35 0 0 0 .1 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23p)'/%3E%3C/svg%3E");
  --fq-drop: rgb(24 25 28 / 0.3);
  --fq-sans: var(--font-sans, "Montserrat", ui-sans-serif, system-ui, sans-serif);
  --fq-type-face: var(--font-mono, ui-monospace, monospace);

  position: relative;
  container: fq / inline-size;
  interpolate-size: allow-keywords;
  background-color: var(--tui-desk);
  background-image:
    linear-gradient(to right, rgba(27, 28, 30, 0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(27, 28, 30, 0.06) 1px, transparent 1px);
  background-size: 40px 40px;
  color: var(--tui-ink);
  font: 400 15px/1.55 var(--fq-sans);
  -webkit-font-smoothing: antialiased;
}
.fq[data-finish='graphite'] {
  color-scheme: dark;
  --tui-desk: #101113;
  background-image:
    linear-gradient(to right, rgba(242, 244, 241, 0.05) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(242, 244, 241, 0.05) 1px, transparent 1px);
  --tui-face: #1b1c1e;
  --tui-face-hi: #28292c;
  --tui-face-lo: #141516;
  --tui-well: #121315;
  --tui-skirt: #09090a;
  --tui-ink: #f2f4f1;
  --tui-ink-2: #a3a7ab;
  --tui-rule: rgb(242 244 241 / 0.11);
  --tui-cap: #ffc929;
  --tui-cap-hi: #ffd34e;
  --tui-cap-skirt: #b38600;
  --tui-cap-ink: #1c1d20;
  --tui-cap-hl: rgb(255 255 255 / 0.45);
  --tui-hl: rgb(255 255 255 / 0.11);
  --tui-well-fill: linear-gradient(to bottom, #070808, var(--tui-well) 45%, #17181a);
  --tui-sh: 0 0 0;
  --tui-sh-a: 0.55;
  --tui-grain: 0.35;
  --tui-focus: #ffc929;
  --fq-drop: rgb(0 0 0 / 0.55);
}
.fq *, .fq *::before, .fq *::after { box-sizing: border-box; }
.fq-head > *, .fq-card p, .fq-ask p { margin: 0; }

.fq-wrap {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.35fr);
  gap: 40px clamp(40px, 6cqi, 104px);
  align-items: start;
  width: min(100% - 2 * clamp(20px, 5cqi, 64px), 1240px);
  margin-inline: auto;
  padding-block: clamp(36px, 5cqi, 64px);
}
.fq-head { position: sticky; top: 24px; padding-top: 34px; }
.fq-head .fq-label {
  margin-bottom: 16px;
  font: 500 12px/1.2 var(--fq-type-face);
  color: #ffc929;
}
.fq-title {
  font: 600 clamp(32px, 4cqi, 52px)/1.04 var(--fq-sans);
  letter-spacing: -0.025em;
  text-wrap: balance;
}
.fq-head .fq-lead { margin-top: 20px; max-width: 36ch; font-size: clamp(15px, 1.3cqi, 17px); color: var(--tui-ink-2); text-wrap: pretty; }

.fq-drawer {
  position: relative;
  isolation: isolate;
  padding: 12px 12px 0;
  border-radius: 14px;
  background: var(--tui-face);
  box-shadow: var(--tui-raised);
}
.fq-drawer::before {
  content: '';
  position: absolute;
  inset: 0;
  z-index: -1;
  border-radius: inherit;
  background: var(--tui-noise), linear-gradient(170deg, rgb(255 255 255 / 0.06), transparent 40%);
  opacity: var(--tui-grain);
  pointer-events: none;
}
.fq-tray {
  display: grid;
  padding: 40px 12px 16px;
  border-radius: 9px 9px 4px 4px;
  background: var(--tui-well-fill) var(--tui-well);
  box-shadow: var(--tui-inset);
}

.fq-card {
  --shade: calc(var(--depth, 0) * 0.11);
  position: relative;
  margin-inline: calc(var(--depth, 0) * 5px);
  border-radius: 4px 4px 1px 1px;
  background:
    linear-gradient(rgb(40 36 26 / var(--shade)), rgb(40 36 26 / var(--shade))),
    var(--fq-fibre),
    var(--fq-paper);
  color: var(--fq-type);
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 0.95),
    inset 0 2px 0 rgb(0 0 0 / 0.05),
    0 -1px 0 rgb(0 0 0 / 0.1),
    0 -7px 10px -5px var(--fq-drop);
  transition: transform 220ms var(--tui-ease), box-shadow 220ms var(--tui-ease);
}
.fq-card:first-child { box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.95), 0 -1px 0 rgb(0 0 0 / 0.08); }
.fq-card:not([open]):hover { transform: translateY(-3px); }
.fq-card[open] {
  z-index: 2;
  margin-top: 9px;
  transform: translateY(-12px);
  box-shadow:
    inset 0 1px 0 rgb(255 255 255 / 0.95),
    0 -5px 9px -5px var(--fq-drop),
    0 22px 30px -16px var(--fq-drop),
    0 2px 3px rgb(0 0 0 / 0.12);
}

.fq-edge {
  display: grid;
  grid-template-columns: 5.2ch minmax(0, 1fr) auto;
  align-items: baseline;
  column-gap: 12px;
  padding: 16px 18px 22px;
  list-style: none;
  cursor: pointer;
  font: 400 15px/22px var(--fq-type-face);
  border-radius: inherit;
  -webkit-tap-highlight-color: transparent;
}
.fq-edge::-webkit-details-marker { display: none; }
.fq-edge::marker { content: ''; }
.fq-edge:focus-visible { outline: 2px solid var(--fq-type); outline-offset: -5px; }
.fq-no { font-size: 11.5px; letter-spacing: 0.04em; color: var(--fq-type-2); }
.fq-q { text-wrap: pretty; }
.fq-mark { width: 12px; height: 12px; align-self: center; position: relative; }
.fq-mark::before, .fq-mark::after { content: ''; position: absolute; left: 1px; right: 1px; top: 5.25px; height: 1.5px; background: var(--fq-type-2); }
.fq-mark::after { transform: rotate(90deg); transition: transform 220ms var(--tui-ease); }
.fq-card[open] .fq-mark::after { transform: rotate(0deg); }

.fq-tab {
  position: absolute;
  bottom: 100%;
  left: calc(var(--tab-at, 0) * 100%);
  height: 19px;
  padding: 3px 11px 0;
  border-radius: 5px 5px 0 0;
  background:
    linear-gradient(rgb(40 36 26 / var(--shade)), rgb(40 36 26 / var(--shade))),
    var(--fq-fibre),
    var(--fq-paper);
  box-shadow: inset 0 1px 0 rgb(255 255 255 / 0.95), 0 -4px 7px -4px var(--fq-drop);
  font: 400 10.5px/16px var(--fq-type-face);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--fq-type-2);
  white-space: nowrap;
  pointer-events: none;
}

.fq-card::details-content {
  block-size: 0;
  overflow: clip;
  transition: block-size 320ms var(--tui-ease), content-visibility 320ms allow-discrete;
}
.fq-card[open]::details-content { block-size: auto; }
.fq-face {
  margin: -8px 18px 0;
  padding: 16px 0 22px calc(5.2ch + 12px);
  border-top: 3px double var(--fq-rule-2);
  font: 400 14px/26px var(--fq-type-face);
  background: repeating-linear-gradient(to bottom, transparent 0 25px, var(--fq-rule) 25px 26px) 0 20px / 100% calc(100% - 42px) no-repeat;
}
.fq-a { max-width: 60ch; }
.fq-filed { margin-top: 26px; font-size: 11px; letter-spacing: 0.06em; color: var(--fq-type-2); text-align: right; }

.fq-front {
  position: relative;
  display: grid;
  justify-items: center;
  gap: 10px;
  margin: 0 -12px;
  padding: 16px 0 18px;
  border-radius: 0 0 14px 14px;
  background: linear-gradient(to bottom, color-mix(in oklab, var(--tui-face-hi) 70%, var(--tui-face)), var(--tui-face));
  box-shadow: inset 0 1px 0 var(--tui-hl), inset 0 2px 0 rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 0.6)), 0 -1px 0 rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 0.9));
}
.fq-holder {
  display: block;
  padding: 3px;
  border-radius: 3px;
  background: linear-gradient(var(--tui-face-lo), var(--tui-face-hi));
  box-shadow: 0 0 0 1px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 1.2)), 0 1px 0 var(--tui-hl), inset 0 1px 1px rgb(0 0 0 / 0.25);
}
.fq-holder-card {
  display: block;
  min-width: 132px;
  padding: 3px 12px 2px;
  border-radius: 1px;
  background: var(--fq-fibre), var(--fq-paper);
  box-shadow: inset 0 1px 2px rgb(0 0 0 / 0.25);
  font: 400 11px/16px var(--fq-type-face);
  letter-spacing: 0.08em;
  text-align: center;
  text-transform: uppercase;
  color: var(--fq-type);
}
.fq-pull {
  display: block;
  width: 108px;
  height: 22px;
  border-radius: 3px 3px 54px 54px / 3px 3px 22px 22px;
  background: var(--tui-well-fill) var(--tui-well);
  box-shadow: var(--tui-inset);
}

.fq-ask {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 14px 24px;
  margin-top: 28px;
  padding-inline: 4px;
}
.fq-note { font-size: 14.5px; color: var(--tui-ink-2); max-width: 44ch; }
.fq-key {
  display: inline-flex;
  align-items: center;
  height: 44px;
  padding: 0 22px;
  border-radius: 9px;
  font: 700 14px/1 var(--fq-sans);
  color: var(--tui-cap-ink);
  text-decoration: none;
  background:
    radial-gradient(120% 90% at 50% 0%, rgb(255 255 255 / 0.1), transparent 60%),
    linear-gradient(var(--tui-cap-hi), var(--tui-cap));
  box-shadow:
    inset 0 1px 0 var(--tui-cap-hl),
    0 3px 0 var(--tui-cap-skirt),
    0 4px 2px rgb(var(--tui-sh) / calc(var(--tui-sh-a) * 1.4)),
    0 9px 14px -6px rgb(var(--tui-sh) / var(--tui-sh-a));
  transition: transform 70ms var(--tui-ease), box-shadow 70ms var(--tui-ease);
}
.fq-key:active { transform: translateY(3px); box-shadow: var(--tui-pressed); }
.fq-key:focus-visible { outline: 2px solid var(--tui-focus); outline-offset: 3px; }

@container fq (max-width: 959px) {
  .fq-wrap { grid-template-columns: minmax(0, 1fr); }
  .fq-head { position: static; padding-top: 0; max-width: 640px; }
}
@container fq (max-width: 559px) {
  .fq-drawer { padding: 8px 8px 0; }
  .fq-tray { padding: 34px 6px 12px; }
  .fq-card { margin-inline: calc(var(--depth, 0) * 3px); }
  .fq-edge { grid-template-columns: minmax(0, 1fr) auto; padding: 14px 14px 20px; font-size: 14px; line-height: 21px; }
  .fq-no { display: none; }
  .fq-tab { font-size: 9.5px; padding-inline: 8px; }
  .fq-face { margin-inline: 14px; padding-left: 0; font-size: 13.5px; }
  .fq-front { margin-inline: -8px; }
  .fq-ask { flex-direction: column; align-items: stretch; }
  .fq-key { justify-content: center; }
}

@media (prefers-reduced-motion: reduce) {
  .fq-card, .fq-mark::after, .fq-key, .fq-card::details-content { transition: none; }
  .fq-card:not([open]):hover { transform: none; }
}
`;
