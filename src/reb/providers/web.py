"""Public website crawler (stdlib only).

- Same host only, robots.txt respected, a page limit and a polite delay.
- No logins, no forms, no captcha handling, no query-string crawling.
- Returns page text plus a technical footprint (CMS, analytics/pixels, chat,
  e-commerce platform) read from the HTML that any visitor receives.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass, field
from html.parser import HTMLParser

USER_AGENT = "REB-desk-scan/0.2 (+https://github.com/samimeseik/reb)"
SKIP_EXT = re.compile(r"\.(pdf|jpe?g|png|gif|webp|svg|zip|rar|mp4|mp3|docx?|xlsx?|pptx?|css|js|ico|xml|json)$", re.I)

FINGERPRINTS = {
    "connect.facebook.net": "Meta Pixel",
    "googletagmanager.com": "Google Tag Manager",
    "google-analytics.com": "Google Analytics",
    "analytics.tiktok.com": "TikTok Pixel",
    "snap.licdn.com": "LinkedIn Insight",
    "static.hotjar.com": "Hotjar",
    "clarity.ms": "Microsoft Clarity",
    "js.hs-scripts.com": "HubSpot",
    "widget.intercom.io": "Intercom",
    "embed.tawk.to": "Tawk.to chat",
    "cdn.shopify.com": "Shopify",
    "wixstatic.com": "Wix",
    "squarespace.com": "Squarespace",
    "js.stripe.com": "Stripe",
    "cdn.salla.network": "Salla",
    "zid.sa": "Zid",
    "ideasoft.com": "IdeaSoft",
    "myikas.com": "ikas",
    "ikas.com/": "ikas",
    "calendly.com": "Calendly",
    "wa.me": "WhatsApp click-to-chat",
    "api.whatsapp.com": "WhatsApp click-to-chat",
}


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []
        self.scripts: list[str] = []
        self.meta: dict[str, str] = {}
        self.title = ""
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript", "svg"):
            self._skip += 1
            if tag == "script" and a.get("src"):
                self.scripts.append(a["src"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag == "meta" and a.get("name") and a.get("content"):
            self.meta[a["name"].lower()] = a["content"]
        if tag == "title":
            self._in_title = True
        if tag in ("p", "div", "li", "h1", "h2", "h3", "h4", "br", "tr", "section", "td", "article"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if not self._skip:
            self.parts.append(data)

    def text(self) -> str:
        raw = re.sub(r"[ \t]+", " ", "".join(self.parts))
        return "\n".join(line.strip() for line in raw.splitlines() if line.strip())


@dataclass
class Page:
    url: str
    title: str
    text: str
    generator: str | None
    scripts: list[str]
    links: list[str]


@dataclass
class Crawl:
    start: str
    pages: list[Page] = field(default_factory=list)
    skipped_by_robots: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _normalize(url: str) -> str:
    if not re.match(r"^https?://", url):
        url = "https://" + url
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc.lower(), parts.path or "/", "", ""))


def _fetch(url: str, timeout: float) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "ar,en;q=0.8,tr;q=0.6"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        ctype = resp.headers.get("Content-Type", "")
        if "html" not in ctype:
            raise ValueError(f"not HTML ({ctype})")
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.geturl(), resp.read(3_000_000).decode(charset, errors="replace")


def crawl(start_url: str, *, max_pages: int = 15, delay: float = 0.5, timeout: float = 20) -> Crawl:
    start = _normalize(start_url)
    host = urllib.parse.urlsplit(start).netloc
    robots = urllib.robotparser.RobotFileParser()
    robots.set_url(f"{urllib.parse.urlsplit(start).scheme}://{host}/robots.txt")
    try:
        robots.read()
    except Exception:  # unreachable robots.txt: treat as allow-all, like browsers and most crawlers
        robots = None
    result = Crawl(start=start)
    queue, seen = [start], {start}
    while queue and len(result.pages) < max_pages:
        url = queue.pop(0)
        if robots is not None and not robots.can_fetch(USER_AGENT, url):
            result.skipped_by_robots.append(url)
            continue
        try:
            final, html = _fetch(url, timeout)
        except Exception as exc:  # noqa: BLE001 — every failure is reported, none is fatal
            result.errors.append(f"{url}: {exc}")
            continue
        parser = _Page()
        parser.feed(html)
        links = []
        for href in parser.links:
            absolute = _normalize(urllib.parse.urljoin(final, href.split("#")[0])) if not href.startswith(("mailto:", "tel:", "javascript:")) else href
            links.append(absolute)
            if (absolute.startswith("http") and urllib.parse.urlsplit(absolute).netloc == host
                    and absolute not in seen and not SKIP_EXT.search(absolute)):
                seen.add(absolute)
                queue.append(absolute)
        result.pages.append(Page(final, parser.title.strip(), parser.text(), parser.meta.get("generator"),
                                 parser.scripts, links))
        time.sleep(delay)
    return result


def footprint(c: Crawl) -> dict[str, list[str]]:
    found: dict[str, set[str]] = {"cms": set(), "tools": set(), "external_hosts": set(), "contact_channels": set()}
    for page in c.pages:
        if page.generator:
            found["cms"].add(page.generator)
        for src in [*page.scripts, *page.links]:
            host = urllib.parse.urlsplit(src).netloc if src.startswith("http") else ""
            target = (host + urllib.parse.urlsplit(src).path) if host else ""
            for marker, name in FINGERPRINTS.items():
                # match against host (+path for host-less markers), never against page words
                if marker in (host if "/" not in marker else target):
                    found["tools"].add(name)
            if host and host != urllib.parse.urlsplit(c.start).netloc and src in page.scripts:
                found["external_hosts"].add(host)
            if src.startswith("mailto:"):
                found["contact_channels"].add("e-mail")
            if src.startswith("tel:"):
                found["contact_channels"].add("phone")
            if "wa.me" in src or "whatsapp" in src:
                found["contact_channels"].add("WhatsApp")
    return {k: sorted(v) for k, v in found.items()}


def mail_provider(domain: str) -> str | None:
    """MX lookup through `dig` when available (no extra dependency)."""
    if not shutil.which("dig"):
        return None
    try:
        out = subprocess.run(["dig", "+short", "MX", domain], capture_output=True, text=True, timeout=10).stdout.lower()
    except (OSError, subprocess.SubprocessError):
        return None
    for marker, name in [("google", "Google Workspace"), ("outlook", "Microsoft 365"), ("zoho", "Zoho Mail"),
                         ("yandex", "Yandex")]:
        if marker in out:
            return name
    hosts = [line.split()[-1].rstrip(".") for line in out.strip().splitlines() if line.strip()]
    if not hosts:
        return None
    return f"self-hosted ({hosts[0]})" if hosts[0].endswith(domain) else hosts[0]
