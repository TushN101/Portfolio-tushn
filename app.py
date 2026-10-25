from flask import Flask, render_template

app = Flask(__name__)

posts_data = [
    (7, "Master API Key Exposure in Website Builder", "Discovered an exposed super-admin API key in client-side requests, enabling full administrative access to user PII, credentials, and site configurations.", "March 31, 2026"),
    (6, "Encrypted File Sharing Website Vulnerability", "Found a bug in the implementation on file encryption leading to full exposure of file shared online", "Feburary 14, 2026"),
    (1, "Critical Information Disclosure Bug in Government Site", "Found a debug mode leaking sensitive site data including source code and environment variables. Reported to CERT-In.", "November 29, 2025"),
    (2, "College Wi-Fi Security Research: Evaluating MAC-Based Access Controls", "An investigation into campus network access control mechanisms, examining the security limitations of MAC address filtering in enterprise wireless environments.", "November 24, 2025"),
    (3, "Exposed Corporate Data on File Sharing Platform", "Identified unauthenticated API endpoints in a file-sharing service, assessing the impact of exposed enterprise credentials and coordinating responsible disclosure.", "July 28, 2024"),
    (4, "Security Assessment of University Mobile App", "Static analysis of an educational mobile application identified hardcoded signing secrets, unauthenticated database endpoints, and cleartext communications.", "N/A"),
    (5, "Public Directory Exposure on Government Website", "Discovered a publicly accessible directory exposing WordPress configuration and database credentials.", "N/A")
]

@app.route('/')
def index():
    return render_template('index.html', posts=posts_data)

@app.route('/posts/<int:id>')
def post_detail(id):
    try:
        return render_template(f"posts/post{id}.html")
    except:
        return "Invalid Post", 404

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
