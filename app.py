import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
import jinja2
from starlette.background import BackgroundTask
from starlette.concurrency import run_in_threadpool
from starlette.templating import Jinja2Templates
from supabase import Client, create_client

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

supabase: Optional[Client] = None
if supabase_url and supabase_key:
    try:
        supabase = create_client(supabase_url, supabase_key)
    except Exception as e:
        print(f"[Warning] Failed to initialize Supabase client: {e}")

project_slug = "blog"


def get_base_url(request: Request) -> str:
    """Determine the canonical base URL, respecting SITE_URL env var or reverse proxy headers."""
    site_url = os.environ.get("SITE_URL")
    if site_url:
        return site_url.rstrip("/")
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get(
        "x-forwarded-host", request.headers.get("host", request.url.netloc)
    )
    return f"{proto}://{host}".rstrip("/")


def send_supabase_log(visited_route: str, remote_ip: str, remote_ua: str) -> None:
    """Synchronous worker function to record visitor analytics in Supabase."""
    try:
        if supabase is None:
            return
        _ = supabase.table("logs").insert({
            "visited_proj": project_slug,
            "visited_route": visited_route,
            "remote_ip": remote_ip,
            "remote_ua": remote_ua,
        }).execute()
    except Exception as e:
        print(f"[Error] Failed to send data  {e}")


async def log_visitor_task(visited_route: str, remote_ip: str, remote_ua: str) -> None:
    """Async background task that runs the synchronous Supabase .execute()
    in a threadpool so it does not block the async event loop."""
    await run_in_threadpool(send_supabase_log, visited_route, remote_ip, remote_ua)


def should_track_request(path: str) -> bool:
    """Check whether the request path should be logged.
    Excludes static assets, /favicon.ico, /robots.txt, and /sitemap.xml."""
    if path in ("/favicon.ico", "/robots.txt", "/sitemap.xml"):
        return False
    if path.endswith(("/favicon.ico", "/robots.txt", "/sitemap.xml")):
        return False
    if "static" in path or path.startswith("/static"):
        return False
    return True


# Initialize FastAPI application
app = FastAPI(title="TushN101")

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Configure Jinja2 templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# Flask-compatible url_for helper in Jinja2 templates (supports filename='...')
@jinja2.pass_context
def custom_url_for(context: dict, name: str, /, **path_params):
    request = context.get("request")
    if name == "static" and "filename" in path_params and "path" not in path_params:
        path_params["path"] = path_params.pop("filename")
    if request is not None:
        return request.url_for(name, **path_params)
    return app.url_path_for(name, **path_params)


templates.env.globals["url_for"] = custom_url_for
templates.env.globals["get_base_url"] = get_base_url


@app.middleware("http")
async def analytics_middleware(request: Request, call_next):
    """Global HTTP middleware for visitor analytics (FastAPI equivalent of Flask's before_request).
    Uses BackgroundTasks so Supabase logging executes after the response is sent."""
    response = await call_next(request)

    try:
        path = request.url.path
        if should_track_request(path):
            remote_ip = (
                request.headers.get("x-real-ip")
                or (
                    request.headers.get("x-forwarded-for", "").split(",")[0].strip()
                    if request.headers.get("x-forwarded-for")
                    else ""
                )
                or (request.client.host if request.client else "")
            )
            remote_ua = request.headers.get("user-agent") or ""

            # Ensure background tasks container is initialized on the response
            if response.background is None:
                response.background = BackgroundTasks()
            elif isinstance(response.background, BackgroundTask) and not isinstance(
                response.background, BackgroundTasks
            ):
                existing_task = response.background
                response.background = BackgroundTasks()
                response.background.tasks.append(existing_task)

            response.background.add_task(
                log_visitor_task, path, remote_ip, remote_ua
            )
    except Exception as e:
        print(f"[Error] Failed to schedule analytics task: {e}")

    return response


# Structured post data: (id, title, preview, date, tag, read_time, thumb, featured, category)
posts_data = [
    (
        7,
        "Master API Key Exposure in Website Builder",
        "Discovered an exposed super-admin API key in client-side requests, enabling full administrative access to user PII, credentials, and site configurations.",
        "March 31, 2026",
        "Broken Authentication",
        "7 min read",
        "/static/post7/image_with_apikey.png",
        True,
        "api",
    ),
    (
        6,
        "Encrypted File Sharing Website Vulnerability",
        "Found a bug in the implementation of file encryption leading to full exposure of files shared online.",
        "February 14, 2026",
        "Cryptography",
        "5 min read",
        "/static/post6/poc.png",
        True,
        "crypto",
    ),
    (
        1,
        "Critical Information Disclosure Bug in Government Site",
        "Found a debug mode leaking sensitive site data including source code and environment variables. Reported to CERT-In.",
        "November 29, 2025",
        "CERT-In Disclosure",
        "4 min read",
        "/static/post1/dashboard_image_1.png",
        True,
        "disclosure",
    ),
    (
        2,
        "College Wi-Fi Security Research: Evaluating MAC-Based Access Controls",
        "An investigation into campus network access control mechanisms, examining the security limitations of MAC address filtering in enterprise wireless environments.",
        "November 24, 2025",
        "Network Security",
        "6 min read",
        "/static/post2/tool_action.png",
        False,
        "network",
    ),
    (
        3,
        "Exposed Corporate Data on File Sharing Platform",
        "Identified unauthenticated API endpoints in a file-sharing service, assessing the impact of exposed enterprise credentials and coordinating responsible disclosure.",
        "July 28, 2024",
        "API Security",
        "5 min read",
        "/static/post3/output.png",
        False,
        "api",
    ),
    (
        4,
        "Security Assessment of University Mobile App",
        "Static analysis of an educational mobile application identified hardcoded signing secrets, unauthenticated database endpoints, and cleartext communications.",
        "August 15, 2024",
        "Mobile AppSec",
        "5 min read",
        "",
        False,
        "mobile",
    ),
    (
        5,
        "Public Directory Exposure on Government Website",
        "Discovered a publicly accessible directory exposing WordPress configuration and database credentials.",
        "June 10, 2024",
        "CERT-In Disclosure",
        "4 min read",
        "/static/post5/directory_listing.png",
        False,
        "disclosure",
    ),
]

POST_DATES = {
    7: "2026-03-31",
    6: "2026-02-14",
    1: "2025-11-29",
    2: "2025-11-24",
    3: "2024-07-28",
    4: "2024-08-15",
    5: "2024-06-10",
}


@app.get("/")
async def index(request: Request):
    base_url = get_base_url(request)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "posts": posts_data,
            "base_url": base_url,
            "canonical_url": f"{base_url}/",
        },
    )


@app.get("/about")
async def about(request: Request):
    base_url = get_base_url(request)
    return templates.TemplateResponse(
        request=request,
        name="about.html",
        context={
            "base_url": base_url,
            "canonical_url": f"{base_url}/about",
        },
    )


@app.get("/contact")
async def contact(request: Request):
    base_url = get_base_url(request)
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={
            "base_url": base_url,
            "canonical_url": f"{base_url}/contact",
        },
    )


@app.get("/posts/{id:int}")
async def post_detail(request: Request, id: int):
    post = next((p for p in posts_data if p[0] == id), None)
    base_url = get_base_url(request)
    canonical_url = f"{base_url}/posts/{id}"
    try:
        return templates.TemplateResponse(
            request=request,
            name=f"posts/post{id}.html",
            context={
                "post": post,
                "base_url": base_url,
                "canonical_url": canonical_url,
            },
        )
    except Exception:
        return HTMLResponse(content="Invalid Post", status_code=404)


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots(request: Request):
    base_url = get_base_url(request)
    content = f"""User-agent: *
Allow: /

# Standard Search Crawlers
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Slurp
Allow: /

User-agent: DuckDuckBot
Allow: /

User-agent: Baiduspider
Allow: /

User-agent: YandexBot
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
    return PlainTextResponse(content=content, media_type="text/plain")


@app.get("/sitemap.xml")
async def sitemap(request: Request):
    base_url = get_base_url(request)

    pages = [
        {
            "loc": f"{base_url}/",
            "changefreq": "weekly",
            "priority": "1.0",
            "lastmod": "2026-03-31",
        },
        {
            "loc": f"{base_url}/about",
            "changefreq": "monthly",
            "priority": "0.8",
            "lastmod": "2026-03-31",
        },
        {
            "loc": f"{base_url}/contact",
            "changefreq": "monthly",
            "priority": "0.7",
            "lastmod": "2026-03-31",
        },
    ]

    for p in posts_data:
        pid = p[0]
        pages.append({
            "loc": f"{base_url}/posts/{pid}",
            "changefreq": "monthly",
            "priority": "0.9",
            "lastmod": POST_DATES.get(pid, "2026-03-31"),
        })

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for page in pages:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{page['loc']}</loc>")
        xml_lines.append(f"    <lastmod>{page['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>{page['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{page['priority']}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")

    xml_content = "\n".join(xml_lines)
    return Response(content=xml_content, media_type="application/xml")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = BASE_DIR / "static" / "favicon.ico"
    if favicon_path.is_file():
        return FileResponse(favicon_path)
    return Response(status_code=204)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
