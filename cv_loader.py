"""
cv_loader.py
Loads and extracts text from Mahdi's CV:
  1. Dynamically from a remote portfolio URL (CV_REMOTE_URL)
  2. From local sibling Web/public directory (during local development)
  3. From local bundled data/cv.pdf or data/cv.txt as fallback
Enriches it with structured portfolio details for the AI Digital Twin system prompt.
"""

import os
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# In-memory cache for CV summary with 5-minute TTL to keep API responses fast
_CV_CACHE = {
    "text": None,
    "last_fetched": 0,
    "source": "none",
}
CACHE_TTL = 300  # 5 minutes in seconds

# Fallback profile details if PDF is empty or being updated
PORTFOLIO_PROFILE = """
## Personal Information
- Full Name: Mahdi Al Sabeh
- Title: Full Stack Developer & Software Engineer
- Location: Beirut, Lebanon
- Email: mahdi.alsabea@gmail.com
- Phone: +961 81 677 521
- GitHub: https://github.com/Mahdi-Al-Sabea
- LinkedIn: https://linkedin.com/in/mahdi-al-sabea-6407a5267
- Summary: Software engineer focused on building robust, premium web/mobile applications, resilient APIs, and AI-integrated systems.

## Education & Degrees
- Master 1 in Informatics: Lebanese University (Beirut, Lebanon) | Sep. 2025 – June 2026
- Bachelor of Computer Science: Antonine University (Baabda, Lebanon) | Sep. 2022 – June 2025

## Professional Experience & Internships
- Web Development Intern @ IDS (Integrated Digital Systems) [June 2025 – July 2025]:
  Built an enterprise Meeting Room Booking & Minutes Management System using Laravel (RESTful API), React.js, and MySQL. Implemented room scheduling with conflict prevention, interactive floor maps, role-based access via Laravel Sanctum (Admin, Employee, Guest), and MoM module with PDF export.
- Web Development Intern @ Vanrise Solutions [April 2025 – June 2025]:
  Developed high-performance RESTful APIs for a telecom reservation system with .NET / C# and SQL Server. Created responsive front-end pages in AngularJS and optimized complex stored procedures and database indexes.

## Core Technical Skills & Tech Stack
- Frontend: React.js, React Native, Expo, Tailwind CSS, Bootstrap, JavaScript (ES6+), TypeScript, HTML5, CSS3, AngularJS
- Backend & APIs: Node.js, Express.js, Laravel (PHP), .NET / C#, RESTful APIs, JWT authentication, Laravel Sanctum, Passport.js
- Databases: PostgreSQL, MySQL, MongoDB, SQL Server
- Cloud, AI & DevOps: Google Gemini AI, Azure Blob Storage, Docker, Git, GitHub

## Highlight Projects
1. Docugov+ (Mobile & Web):
   E-Government document verification platform. Mukhtar-based document workflow (Civil Status Extract, Birth Certificate). React Native Expo mobile app, React admin panel, Express.js & PostgreSQL, Google Gemini AI image verification, Azure Blob storage, QR scanning, bilingual & dark mode.
2. Beep Beep (Full Stack):
   On-demand delivery & fleet management web application. Laravel RESTful backend, MySQL, responsive frontend. Driver auto-assignment, OTP sign-in, live chat, multi-role RBAC, Google OAuth, Stripe payments.
3. Meeting Room Booking & MoM System (Full Stack):
   Enterprise room scheduling with interactive floor maps, conflict detection, Google Gemini AI image verification, Laravel Sanctum auth, PDF summaries.
4. Task Management Platform (.NET + React):
   Full-stack Kanban & task tracking system with .NET REST API, React.js frontend, JWT auth, and MySQL.
5. Rental Listing Platform:
   Property rentals for web and mobile (React.js, React Native, Node.js, MongoDB, malware scanning with OPWAST Cloud Defender).
6. E-Commerce Platform:
   Dynamic store with CodeIgniter / PHP, MySQL, AJAX, DummyJSON API integration.
7. Store Management System:
   Desktop POS and inventory management system in JavaFX with MySQL and RBAC.
"""


def extract_pdf_text(source) -> str:
    """Extracts raw text from a PDF file path or bytes using pypdf."""
    try:
        from io import BytesIO
        from pypdf import PdfReader

        if isinstance(source, (bytes, bytearray)):
            reader = PdfReader(BytesIO(source))
        else:
            reader = PdfReader(str(source))

        extracted_pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                extracted_pages.append(f"--- Page {i + 1} ---\n{text.strip()}")
        return "\n\n".join(extracted_pages)
    except Exception as e:
        print(f"[Warning] Could not extract text from PDF: {e}")
        return ""


def fetch_remote_cv(url: str) -> str:
    """
    Fetches the latest CV PDF from a public URL (e.g. your live portfolio).
    Saves a local cached copy in data/cached_remote_cv.pdf for offline resilience.
    """
    try:
        import urllib.request

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status == 200:
                data = response.read()
                if data and len(data) > 100:
                    try:
                        DATA_DIR.mkdir(parents=True, exist_ok=True)
                        (DATA_DIR / "cached_remote_cv.pdf").write_bytes(data)
                    except Exception as err:
                        print(f"[Warning] Could not write cached_remote_cv.pdf: {err}")

                    extracted = extract_pdf_text(data)
                    if extracted:
                        print(f"[Info] Successfully loaded CV from remote URL: {url}")
                        return extracted
    except Exception as e:
        print(f"[Warning] Could not fetch remote CV from {url}: {e}")
    return ""


def get_cv_summary(force_refresh: bool = False) -> str:
    """
    Builds the complete profile summary to inject into the system prompt.
    Prioritizes:
      1. Remote URL (CV_REMOTE_URL) from live portfolio (auto-sync)
      2. Local sibling Web portfolio PDF (for local development)
      3. Bundled data/cv.pdf or data/cv.txt fallback
      4. Structured portfolio profile
    Results are cached in memory for 5 minutes to maintain fast API response times.
    """
    current_time = time.time()
    if not force_refresh and _CV_CACHE["text"] and (current_time - _CV_CACHE["last_fetched"] < CACHE_TTL):
        return _CV_CACHE["text"]

    summary_parts = []
    cv_extracted = False
    source_used = "portfolio_profile_only"

    # 1. Check for manual cv_summary.txt if user provided custom notes
    txt_path = DATA_DIR / "cv_summary.txt"
    if txt_path.exists():
        try:
            custom_text = txt_path.read_text(encoding="utf-8").strip()
            if custom_text:
                summary_parts.append(f"# Custom CV Notes:\n{custom_text}")
        except Exception as e:
            print(f"[Warning] Error reading cv_summary.txt: {e}")

    # 2. Try fetching from remote portfolio URL if configured
    remote_url = os.getenv("CV_REMOTE_URL", "").strip()
    if remote_url:
        remote_text = fetch_remote_cv(remote_url)
        if remote_text:
            summary_parts.append(f"# Latest CV Details (from {remote_url}):\n{remote_text}")
            cv_extracted = True
            source_used = f"remote: {remote_url}"

    # 3. Check for cached remote CV from previous successful fetch if current fetch failed
    cached_pdf = DATA_DIR / "cached_remote_cv.pdf"
    if not cv_extracted and cached_pdf.exists():
        cached_text = extract_pdf_text(cached_pdf)
        if cached_text:
            summary_parts.append(f"# Cached Remote CV Details:\n{cached_text}")
            cv_extracted = True
            source_used = "cached_remote_cv.pdf"

    # 4. Check for local sibling Web project PDF (ideal for local development)
    if not cv_extracted:
        web_public_candidates = [
            BASE_DIR.parent / "Web" / "public" / "Mahdi-Al-Sabeh CV.pdf",
            BASE_DIR.parent / "Web" / "public" / "cv.pdf",
        ]
        for candidate in web_public_candidates:
            if candidate.exists():
                text = extract_pdf_text(candidate)
                if text:
                    summary_parts.append(f"# CV Details (from local Web/public/{candidate.name}):\n{text}")
                    cv_extracted = True
                    source_used = f"local_web: {candidate.name}"
                    break

    # 5. Check for bundled data/cv.pdf or data/cv.txt
    if not cv_extracted:
        cv_pdf_path = DATA_DIR / "cv.pdf"
        cv_txt_path = DATA_DIR / "cv.txt"
        if cv_pdf_path.exists():
            text = extract_pdf_text(cv_pdf_path)
            if text:
                summary_parts.append(f"# CV Details:\n{text}")
                cv_extracted = True
                source_used = "data/cv.pdf"
        elif cv_txt_path.exists():
            try:
                cv_text = cv_txt_path.read_text(encoding="utf-8").strip()
                if cv_text:
                    summary_parts.append(f"# CV Details:\n{cv_text}")
                    cv_extracted = True
                    source_used = "data/cv.txt"
            except Exception as e:
                print(f"[Warning] Error reading cv.txt: {e}")

    # 6. Always include the structured portfolio profile for high accuracy
    summary_parts.append(f"# Verified Background & Portfolio Knowledge Base:\n{PORTFOLIO_PROFILE.strip()}")

    full_summary = "\n\n".join(summary_parts)
    _CV_CACHE["text"] = full_summary
    _CV_CACHE["last_fetched"] = current_time
    _CV_CACHE["source"] = source_used

    return full_summary


if __name__ == "__main__":
    import sys
    # Ensure UTF-8 output on Windows consoles
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8")
    summary = get_cv_summary()
    print("--- Loaded Summary Preview ---")
    print(f"Active Source: {_CV_CACHE['source']}")
    print(f"Summary total characters: {len(summary)}")
    print(summary[:300].encode("ascii", errors="replace").decode("ascii") + "...")
