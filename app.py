from flask import Flask, render_template


app = Flask(__name__)


## -- spazy ---
## -- start of code -- 
from supabase import create_client , Client
from flask import request
from dotenv import load_dotenv
import os

load_dotenv()

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

project_slug = "blog"

@app.before_request
def spazzy():
    try:
        if "static" not in request.path:
            _ = supabase.table("logs").insert({
                "visited_proj": project_slug,
                "visited_route": request.path,
                "remote_ip": request.headers.get("x-real-ip") or "",
                "remote_ua": request.headers.get('User-Agent') or ""
            }).execute()
    except Exception as e:
        print(f"[Error] Failed to send data  {e}")
        pass    
# -- end of code --  

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
        "api"
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
        "crypto"
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
        "disclosure"
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
        "network"
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
        "api"
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
        "mobile"
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
        "disclosure"
    )
]

@app.route('/')
def index():
    return render_template('index.html', posts=posts_data)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/posts/<int:id>')
def post_detail(id):
    try:
        return render_template(f"posts/post{id}.html")
    except:
        return "Invalid Post", 404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
