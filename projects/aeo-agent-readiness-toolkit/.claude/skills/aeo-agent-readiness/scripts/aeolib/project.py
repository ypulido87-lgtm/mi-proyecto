"""Local repository inspection: stack, site type and real capability evidence.

Applicability is decided here. Every capability verdict carries the evidence
that produced it, so a check is only ever N/A because nothing was found, never
because a list was hard-coded to N/A.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

IGNORED_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "bower_components", "__pycache__",
    ".venv", "venv", "env", ".tox", "dist", "build", "out", ".next", ".nuxt", ".svelte-kit",
    ".cache", ".parcel-cache", "coverage", ".pytest_cache", ".mypy_cache", ".idea", ".vscode",
    "target", "bin", "obj", ".terraform", ".serverless", "tmp", ".tmp",
    # Agent tooling describes how the site is audited, never what it offers.
    ".claude", ".cursor", ".github",
}
TEXT_SUFFIXES = {
    ".html", ".htm", ".xhtml", ".php", ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".vue",
    ".svelte", ".astro", ".py", ".rb", ".go", ".rs", ".java", ".cs", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".xml", ".md", ".mdx", ".txt", ".twig", ".liquid", ".erb", ".hbs", ".ejs",
    ".conf", ".htaccess", ".env.example",
}
MAX_SCAN_FILES = 20_000
MAX_TEXT_BYTES = 400_000

STACK_MARKERS = [
    ("WordPress", ["wp-config.php", "wp-content", "wp-load.php"], []),
    ("Joomla", ["configuration.php", "administrator/index.php"], []),
    ("Drupal", ["core/lib/Drupal.php", "sites/default/settings.php"], []),
    ("Next.js", ["next.config.js", "next.config.mjs", "next.config.ts"], ["next"]),
    ("Nuxt", ["nuxt.config.js", "nuxt.config.ts"], ["nuxt"]),
    ("Astro", ["astro.config.mjs", "astro.config.ts"], ["astro"]),
    ("SvelteKit", ["svelte.config.js"], ["@sveltejs/kit"]),
    ("Gatsby", ["gatsby-config.js", "gatsby-config.ts"], ["gatsby"]),
    ("Remix", ["remix.config.js"], ["@remix-run/react"]),
    ("Vite", ["vite.config.js", "vite.config.ts"], ["vite"]),
    ("React", [], ["react"]),
    ("Vue", [], ["vue"]),
    ("Angular", ["angular.json"], ["@angular/core"]),
    ("Hugo", ["hugo.toml", "config.toml", "hugo.yaml"], []),
    ("Jekyll", ["_config.yml"], []),
    ("Eleventy", [".eleventy.js", "eleventy.config.js"], ["@11ty/eleventy"]),
    ("Django", ["manage.py"], []),
    ("Flask/FastAPI", [], ["flask", "fastapi"]),
    ("Laravel", ["artisan"], []),
    ("Symfony", ["symfony.lock"], []),
    ("Rails", ["Gemfile", "config/routes.rb"], []),
    ("Express", [], ["express"]),
    ("Node.js", ["package.json"], []),
    ("Python", ["requirements.txt", "pyproject.toml", "Pipfile"], []),
    ("PHP", ["composer.json", "index.php"], []),
]

HOSTING_MARKERS = {
    "Vercel": ["vercel.json", ".vercel"],
    "Netlify": ["netlify.toml", "_headers", "_redirects"],
    "Cloudflare Pages/Workers": ["wrangler.toml", "wrangler.json", "wrangler.jsonc"],
    "Apache": [".htaccess", "httpd.conf"],
    "Nginx": ["nginx.conf"],
    "IIS": ["web.config"],
    "Docker": ["Dockerfile", "docker-compose.yml"],
    "GitHub Pages": [".nojekyll"],
    "AWS Amplify": ["amplify.yml"],
}

COMMERCE_DEPENDENCIES = [
    "stripe", "@stripe/stripe-js", "braintree", "paypal", "@paypal/react-paypal-js",
    "square", "adyen", "mollie", "razorpay", "snipcart", "commerce.js", "@chec/commerce.js",
    "shopify", "@shopify/hydrogen", "shopify-buy", "medusa", "@medusajs/medusa",
    "saleor", "woocommerce", "bigcommerce", "swell-js", "lemonsqueezy", "paddle",
]
COMMERCE_PATH_TOKENS = ["cart", "checkout", "basket", "product", "products", "shop", "store", "pricing", "order", "orders", "payment", "subscribe", "subscription", "booking", "reservation"]
# Operational call sites only. A page that mentions Stripe, or a config listing
# supported providers, is documentation about payments, not a payment integration.
COMMERCE_CODE_MARKERS = re.compile(
    r"(addToCart\s*\(|add_to_cart\s*\(|checkout\.sessions\.create|paymentIntents\.create|"
    r"payment_intents\.create|new\s+Stripe\s*\(|stripe\.checkout|WC\(\)->cart|woocommerce_add|"
    r"line_items\s*[:=]|paypal\.Buttons\s*\(|braintree\.\w+\.create|createOrder\s*\(|"
    r"data-item-price)", re.I,
)

API_FILE_MARKERS = ["openapi.json", "openapi.yaml", "openapi.yml", "swagger.json", "swagger.yaml", "schema.graphql", "asyncapi.yaml", "api-catalog"]
API_DEPENDENCIES = ["express", "fastify", "koa", "hapi", "fastapi", "flask", "django-rest-framework", "djangorestframework", "graphql", "apollo-server", "@nestjs/core", "hono"]
API_PATH_TOKENS = ["/api/", "\\api\\", "routes", "controllers", "endpoints", "handlers"]

AUTH_DEPENDENCIES = ["next-auth", "@auth/core", "passport", "oidc-provider", "openid-client", "authlib", "django-allauth", "oauthlib", "keycloak", "auth0", "@clerk/nextjs", "supabase", "firebase-auth", "lucia"]
# Likewise: an endpoint path string, or a reference to RFC 8414, is not an
# OAuth implementation. Require tokens that only appear in real auth code.
AUTH_CODE_MARKERS = re.compile(
    r"\b(grant_type|authorization_code|client_credentials|client_secret|jwks_uri|"
    r"access_token|refresh_token|id_token|NextAuth\s*\(|passport\.use|"
    r"OAuth2[A-Za-z]*\s*\()", re.I,
)

MCP_MARKERS = ["mcp.json", "mcp_server", "modelcontextprotocol", "@modelcontextprotocol/sdk", "fastmcp"]
AGENT_MARKERS = ["agent-card.json", "a2a", "webmcp", "agent-skills"]

HTML_EXTENSIONS = {".html", ".htm", ".xhtml"}
TEMPLATE_EXTENSIONS = {".twig", ".liquid", ".erb", ".hbs", ".ejs", ".astro", ".vue", ".svelte", ".php", ".jsx", ".tsx"}
MARKDOWN_EXTENSIONS = {".md", ".mdx", ".markdown"}
# Markdown counts as web content only when something publishes it.
SITE_GENERATORS = {"Hugo", "Jekyll", "Astro", "Eleventy", "Gatsby", "Next.js", "Nuxt", "SvelteKit", "Docusaurus", "Remix"}


@dataclass
class Evidence:
    """One capability verdict plus the artifacts that justify it."""

    present: bool = False
    items: list[str] = field(default_factory=list)

    def add(self, item: str) -> None:
        if item not in self.items:
            self.items.append(item)
        self.present = True

    def to_dict(self) -> dict[str, Any]:
        return {"present": self.present, "evidence": self.items[:12]}


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def scan_files(root: Path) -> list[Path]:
    """Walk the project, skipping vendored, build and VCS directories."""
    found: list[Path] = []
    stack = [root]
    while stack and len(found) < MAX_SCAN_FILES:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except (PermissionError, OSError):
            continue
        for entry in entries:
            try:
                if entry.is_dir():
                    if entry.name not in IGNORED_DIRS:
                        stack.append(entry)
                elif entry.is_file():
                    found.append(entry)
            except OSError:
                continue
    return found


def read_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return ""


def _dependencies(root: Path, files: list[Path]) -> set[str]:
    deps: set[str] = set()
    for path in files:
        name = path.name.lower()
        if name == "package.json":
            try:
                data = json.loads(read_text(path) or "{}")
            except json.JSONDecodeError:
                continue
            for key in ("dependencies", "devDependencies", "peerDependencies"):
                deps.update(k.lower() for k in (data.get(key) or {}))
        elif name in ("requirements.txt", "pipfile"):
            for line in read_text(path).splitlines():
                token = re.split(r"[=<>\[; ]", line.strip(), 1)[0].lower()
                if token and not token.startswith("#"):
                    deps.add(token)
        elif name == "pyproject.toml":
            deps.update(m.lower() for m in re.findall(r'^\s*"?([A-Za-z0-9_.\-]+)"?\s*[=><~^]', read_text(path), re.M))
        elif name == "composer.json":
            try:
                data = json.loads(read_text(path) or "{}")
            except json.JSONDecodeError:
                continue
            deps.update(k.lower() for k in (data.get("require") or {}))
            deps.update(k.lower() for k in (data.get("require-dev") or {}))
    return deps


def detect_stack(root: Path, files: list[Path], deps: set[str]) -> dict[str, Any]:
    relatives = {_rel(p, root).lower() for p in files}
    names = {p.name.lower() for p in files}
    detected: list[str] = []
    for stack_name, file_markers, dep_markers in STACK_MARKERS:
        hit = any(m.lower() in names or any(r.endswith(m.lower()) or m.lower() in r for r in relatives) for m in file_markers)
        hit = hit or any(d in deps for d in dep_markers)
        if hit:
            detected.append(stack_name)
    if not detected and any(p.suffix.lower() in (".html", ".htm") for p in files):
        detected.append("Static HTML")
    hosting = [name for name, markers in HOSTING_MARKERS.items() if any(m.lower() in names or any(m.lower() in r for r in relatives) for m in markers)]
    return {"frameworks": detected or ["Unknown"], "hosting": hosting, "dependency_count": len(deps)}


def detect_capabilities(root: Path, files: list[Path], deps: set[str], frameworks: list[str] | None = None) -> dict[str, Any]:
    """Detect real capabilities. Everything here gates an applicability decision."""
    relatives = [_rel(p, root) for p in files]
    lower_relatives = [r.lower() for r in relatives]
    names = {p.name.lower() for p in files}

    commerce, api, auth, mcp, agent = Evidence(), Evidence(), Evidence(), Evidence(), Evidence()
    content = Evidence()
    markdown_files: list[str] = []

    for dep in sorted(deps):
        if any(marker in dep for marker in COMMERCE_DEPENDENCIES):
            commerce.add("dependency: " + dep)
        if dep in API_DEPENDENCIES:
            api.add("dependency: " + dep)
        if any(marker in dep for marker in AUTH_DEPENDENCIES):
            auth.add("dependency: " + dep)
        if any(marker in dep for marker in MCP_MARKERS):
            mcp.add("dependency: " + dep)

    for path, relative, lower in zip(files, relatives, lower_relatives):
        suffix = path.suffix.lower()
        if path.name.lower() in [m.lower() for m in API_FILE_MARKERS]:
            api.add("file: " + relative)
        if any(token in lower for token in API_PATH_TOKENS) and suffix in TEXT_SUFFIXES:
            api.add("path: " + relative)
        segments = [s for s in lower.split("/") if s]
        if any(seg.split(".")[0] in COMMERCE_PATH_TOKENS for seg in segments):
            commerce.add("path: " + relative)
        if any(marker in lower for marker in MCP_MARKERS):
            mcp.add("path: " + relative)
        if any(marker in lower for marker in AGENT_MARKERS):
            agent.add("path: " + relative)
        if suffix in HTML_EXTENSIONS:
            content.add("html: " + relative)
        elif suffix in TEMPLATE_EXTENSIONS:
            content.add("template: " + relative)
        elif suffix in MARKDOWN_EXTENSIONS:
            markdown_files.append(relative)

    # Content-level confirmation keeps directory-name coincidences from
    # promoting a marketing page into a real commerce or auth capability.
    code_suffixes = TEXT_SUFFIXES - {".md", ".mdx", ".txt", ".rst"}
    inspectable = [p for p in files if p.suffix.lower() in code_suffixes][:1500]
    commerce_confirmed = False
    auth_confirmed = False
    for path in inspectable:
        text = read_text(path)
        if not text:
            continue
        if not commerce_confirmed and COMMERCE_CODE_MARKERS.search(text):
            commerce.add("code marker in " + _rel(path, root))
            commerce_confirmed = True
        if not auth_confirmed and AUTH_CODE_MARKERS.search(text):
            auth.add("auth marker in " + _rel(path, root))
            auth_confirmed = True
        if commerce_confirmed and auth_confirmed:
            break

    # A repository of Markdown files is not a website unless a generator publishes it.
    has_generator = bool(set(frameworks or []) & SITE_GENERATORS)
    if markdown_files and (has_generator or content.present):
        for relative in markdown_files[:12]:
            content.add("markdown: " + relative)

    published = {
        "robots.txt": [r for r in relatives if r.lower().endswith("robots.txt")],
        "sitemap.xml": [r for r in relatives if re.search(r"sitemap[^/]*\.xml$", r.lower())],
        "llms.txt": [r for r in relatives if r.lower().endswith("llms.txt")],
        "llms-full.txt": [r for r in relatives if r.lower().endswith("llms-full.txt")],
        "well_known": [r for r in relatives if ".well-known/" in r.lower()],
    }

    return {
        "markdown_files": len(markdown_files),
        "site_generator_detected": has_generator,
        "commerce": {**commerce.to_dict(), "code_confirmed": commerce_confirmed},
        "api": api.to_dict(),
        "auth": {**auth.to_dict(), "code_confirmed": auth_confirmed},
        "mcp": mcp.to_dict(),
        "agent_service": agent.to_dict(),
        "content": content.to_dict(),
        "published_files": published,
        "has_html": any(n.endswith((".html", ".htm")) for n in names),
    }


def classify_site(capabilities: dict[str, Any]) -> str:
    """Content Site, API / Application, Hybrid or Unknown, from real evidence."""
    content_files = len(capabilities["content"]["evidence"])
    api_present = capabilities["api"]["present"]
    strong_api = api_present and len(capabilities["api"]["evidence"]) >= 3
    has_content = capabilities["content"]["present"] and content_files >= 1
    if has_content and strong_api:
        return "Hybrid"
    if strong_api and not has_content:
        return "API / Application"
    if has_content:
        return "Content Site"
    if api_present:
        return "API / Application"
    return "Unknown"


def find_html_documents(root: Path, files: list[Path], limit: int = 25) -> list[Path]:
    """Pick representative served HTML files, preferring index/home documents."""
    html = [p for p in files if p.suffix.lower() in (".html", ".htm")]

    def rank(path: Path) -> tuple[int, int]:
        relative = _rel(path, root).lower()
        score = 0
        if relative in ("index.html", "public/index.html", "dist/index.html"):
            score -= 10
        if path.name.lower() == "index.html":
            score -= 5
        score += relative.count("/")
        return (score, len(relative))

    return sorted(html, key=rank)[:limit]


def inspect(root: Path) -> dict[str, Any]:
    files = scan_files(root)
    deps = _dependencies(root, files)
    stack = detect_stack(root, files, deps)
    capabilities = detect_capabilities(root, files, deps, stack["frameworks"])
    return {
        "root": str(root),
        "file_count": len(files),
        "truncated": len(files) >= MAX_SCAN_FILES,
        "stack": stack,
        "capabilities": capabilities,
        "site_type": classify_site(capabilities),
        "html_documents": [_rel(p, root) for p in find_html_documents(root, files)],
    }
