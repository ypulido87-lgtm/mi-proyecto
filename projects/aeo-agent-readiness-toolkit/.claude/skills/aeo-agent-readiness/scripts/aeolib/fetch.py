"""HTTP inspection: real status codes, redirect chains, headers and bodies.

`urlopen` follows redirects silently and raises on 4xx/5xx, which destroys the
evidence an audit needs. This layer keeps the status of every hop and never
turns an HTTP error into an exception.
"""
from __future__ import annotations

import gzip
import ssl
import zlib
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

USER_AGENT = "AEO-Agent-Readiness-Toolkit/2.0 (+audit; respects robots)"
MAX_BODY = 3_000_000
DEFAULT_TIMEOUT = 15


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D102
        return None


_OPENER = build_opener(_NoRedirect)

# TLS verification failures are an environment condition (a corporate proxy, a
# stale trust store), not a property of the audited site. They are reported
# distinctly so they never become a false P0 "site is down" finding.
_INSECURE_OPENER = None
TLS_VERIFY_MARKER = "CERTIFICATE_VERIFY_FAILED"


def set_insecure_tls(enabled: bool) -> None:
    """Opt out of certificate verification for diagnostics only.

    Never use the result of an insecure fetch as a security conclusion; the
    audit report stamps every run made with verification disabled.
    """
    global _INSECURE_OPENER
    if not enabled:
        _INSECURE_OPENER = None
        return
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    _INSECURE_OPENER = build_opener(_NoRedirect, HTTPSHandler(context=context))


def is_tls_verification_error(response: "Response") -> bool:
    return bool(response.error and TLS_VERIFY_MARKER in response.error)


@dataclass
class Response:
    url: str
    status: int | None = None
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes = b""
    error: str | None = None
    redirects: list[dict[str, Any]] = field(default_factory=list)
    tls_verification_failed: bool = False
    elapsed_hops: int = 0

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300

    @property
    def content_type(self) -> str:
        return (self.headers.get("Content-Type") or "").lower()

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", "replace")

    def header(self, name: str) -> str:
        for key, value in self.headers.items():
            if key.lower() == name.lower():
                return value
        return ""

    def to_dict(self, include_body: bool = False) -> dict[str, Any]:
        data = {
            "url": self.url,
            "status": self.status,
            "headers": self.headers,
            "redirects": self.redirects,
            "bytes": len(self.body),
            "error": self.error,
        }
        if include_body:
            data["body"] = self.text
        return data


def _decode(raw: bytes, encoding: str) -> bytes:
    encoding = (encoding or "").lower()
    try:
        if "gzip" in encoding:
            return gzip.decompress(raw)
        if "deflate" in encoding:
            return zlib.decompress(raw, -zlib.MAX_WBITS)
    except Exception:
        return raw
    return raw


def _single(url: str, accept: str, method: str, user_agent: str, timeout: int) -> Response:
    request = Request(
        url,
        method=method,
        headers={"User-Agent": user_agent, "Accept": accept, "Accept-Encoding": "gzip, deflate"},
    )
    opener = _INSECURE_OPENER or _OPENER
    try:
        with opener.open(request, timeout=timeout) as raw:
            headers = dict(raw.headers)
            body = b"" if method == "HEAD" else raw.read(MAX_BODY)
            return Response(url, raw.status, headers, _decode(body, raw.headers.get("Content-Encoding", "")))
    except HTTPError as exc:  # 3xx handled here because redirects are disabled
        headers = dict(exc.headers or {})
        try:
            body = b"" if method == "HEAD" else exc.read(MAX_BODY)
        except Exception:
            body = b""
        return Response(url, exc.code, headers, _decode(body, headers.get("Content-Encoding", "")))
    except (URLError, OSError, ValueError) as exc:
        message = f"{type(exc).__name__}: {exc}"
        return Response(url, None, {}, b"", error=message, tls_verification_failed=TLS_VERIFY_MARKER in message)


def fetch(
    url: str,
    accept: str = "text/html,application/xhtml+xml",
    method: str = "GET",
    user_agent: str = USER_AGENT,
    timeout: int = DEFAULT_TIMEOUT,
    max_redirects: int = 5,
) -> Response:
    """Fetch a URL, recording every redirect hop instead of hiding it."""
    if urlsplit(url).scheme not in ("http", "https"):
        return Response(url, None, {}, b"", error="Unsupported scheme; only http/https are audited")
    chain: list[dict[str, Any]] = []
    current = url
    for _ in range(max_redirects + 1):
        response = _single(current, accept, method, user_agent, timeout)
        if response.status in (301, 302, 303, 307, 308) and response.header("Location"):
            target = urljoin(current, response.header("Location"))
            chain.append({"from": current, "status": response.status, "to": target})
            current = target
            continue
        response.redirects = chain
        response.elapsed_hops = len(chain)
        return response
    final = Response(current, None, {}, b"", error="Too many redirects")
    final.redirects = chain
    return final


def origin(url: str) -> str:
    parts = urlsplit(url if "://" in url else f"https://{url}")
    return f"{parts.scheme}://{parts.netloc}/"
