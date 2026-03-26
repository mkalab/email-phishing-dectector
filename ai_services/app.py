from fastapi import FastAPI, UploadFile, File, HTTPException
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from email import policy
from email.parser import BytesParser
import re, os, json
import uvicorn

app = FastAPI(title="AI Phishing Shield")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
device   = "cuda" if torch.cuda.is_available() else "cpu"

# ════════════════════════════════════════════════════════════
# LOAD MODELS
# ════════════════════════════════════════════════════════════
EMAIL_MODEL_PATH = os.path.join(BASE_DIR, "phishing_classifier_final")
email_tokenizer  = None
email_model      = None
try:
    email_tokenizer = AutoTokenizer.from_pretrained(EMAIL_MODEL_PATH, local_files_only=True)
    email_model     = AutoModelForSequenceClassification.from_pretrained(EMAIL_MODEL_PATH, local_files_only=True)
    email_model.to(device).eval()
    print(f"✅ Email model loaded on {device}")
except Exception as e:
    print(f"⚠️  Email model error: {e}")

URL_MODEL_PATH = os.path.join(BASE_DIR, "url_phishing_classifier_final")
rf_model       = None
rf_features    = None
rf_threshold   = 0.5

try:
    import joblib
    import pandas as pd
    import tldextract as _tldextract
    _rf_deps_ok = True
except ImportError:
    _rf_deps_ok = False
    print("⚠️  Thiếu deps RF: pip install joblib pandas tldextract")

if _rf_deps_ok:
    try:
        rf_model    = joblib.load(os.path.join(URL_MODEL_PATH, "rf_model.joblib"))
        rf_features = joblib.load(os.path.join(URL_MODEL_PATH, "feature_names.joblib"))
        cfg_path    = os.path.join(URL_MODEL_PATH, "config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path) as f:
                rf_threshold = float(json.load(f).get("optimal_threshold", 0.5))
        print(f"✅ URL RF model loaded | {len(rf_features)} features | threshold={rf_threshold}")
    except Exception as e:
        print(f"⚠️  URL RF model error: {e}")


# ════════════════════════════════════════════════════════════
# FEATURE EXTRACTION (phục vụ RF model — không thay đổi)
# ════════════════════════════════════════════════════════════
def _extract_url_features(url: str) -> dict:
    import math
    url = str(url)
    try:
        ext = _tldextract.extract(url)
        domain, suffix, subdomain = ext.domain, ext.suffix, ext.subdomain
    except Exception:
        domain = suffix = subdomain = ''

    path      = re.sub(r'https?://[^/]+', '', url)
    url_lower = url.lower()
    dom_lower = domain.lower()

    def _entropy(s):
        if not s: return 0.0
        freq = {}
        for c in s: freq[c] = freq.get(c, 0) + 1
        n = len(s)
        return -sum((v/n)*math.log2(v/n) for v in freq.values())

    consonants = set('bcdfghjklmnpqrstvwxyz')
    dom_alpha  = [c for c in dom_lower if c.isalpha()]

    _SUSPICIOUS_WORDS = [
        'login','signin','logon','verify','secure','account','update','confirm',
        'bank','payment','pay','invoice','credit','wallet','crypto',
        'urgent','alert','suspend','expire','locked','free','prize','password','otp',
    ]


    return {
        'url_length':            len(url),
        'domain_length':         len(domain),
        'path_length':           len(path),
        'query_length':          len(url.split('?')[1]) if '?' in url else 0,
        'num_dots':              url.count('.'),
        'num_hyphens':           url.count('-'),
        'num_underscores':       url.count('_'),
        'num_slashes':           url.count('/'),
        'num_question':          url.count('?'),
        'num_ampersand':         url.count('&'),
        'num_equal':             url.count('='),
        'num_at':                url.count('@'),
        'num_percent':           url.count('%'),
        'num_hash':              url.count('#'),
        'num_tilde':             url.count('~'),
        'num_subdomains':        len([s for s in subdomain.split('.') if s]),
        'has_ip':                int(bool(re.match(r'\d{1,3}(\.\d{1,3}){3}', url))),
        'domain_has_digit':      int(bool(re.search(r'\d', domain))),
        'domain_has_hyphen':     int('-' in domain),
        'domain_dot_count':      domain.count('.'),
        'digit_ratio':           sum(c.isdigit() for c in url) / max(len(url), 1),
        'special_ratio':         sum(not c.isalnum() for c in url) / max(len(url), 1),
        'uppercase_ratio':       sum(c.isupper() for c in url) / max(len(url), 1),
        'letter_ratio':          sum(c.isalpha() for c in url) / max(len(url), 1),
        'is_https':              int(url.startswith('https')),
        'tld_length':            len(suffix),
        'is_common_tld':         int(suffix in ['com','org','net','edu','gov']),
        'is_suspicious_tld':     int(suffix in ['tk','ml','ga','cf','gq','xyz','top','pw']),
        'suspicious_word_count': sum(1 for w in _SUSPICIOUS_WORDS if w in url_lower),
        'has_login_word':        int(any(w in url_lower for w in ['login','signin','logon'])),
        'has_verify_word':       int(any(w in url_lower for w in ['verify','confirm','validate'])),
        'has_secure_word':       int('secure' in url_lower),
        'has_bank_word':         int(any(w in url_lower for w in ['bank','paypal','visa','mastercard'])),
        'num_tokens':            len(re.split(r'[/\-_?=&.]', url)),
        'max_token_length':      max((len(t) for t in re.split(r'[/\-_?=&.]', url) if t), default=0),
        'has_port':              int(bool(re.search(r':\d{2,5}[/\s]', url))),
        'double_slash_in_path':  int('//' in path),
        'url_depth':             len([p for p in path.split('/') if p]),
        'has_redirect':          int(url.count('http') > 1),
        'domain_entropy':        round(_entropy(domain), 4),
        'is_long_url':           int(len(url) > 75),
        'brand_in_url':          0,
        'brand_in_domain':       0,
        'brand_in_subdomain':    0,
        'has_suspicious_brand':  0,
        'has_typo_brand':        0,
        'has_unicode_domain':    int(not domain.isascii()),
        'is_short_domain':       int(len(domain) <= 3),
        'consonant_ratio':       round(sum(1 for c in dom_alpha if c in consonants) / max(len(dom_alpha), 1), 4),
        'digit_sequence':        int(bool(re.search(r'\d{3,}', domain))),
    }


# ════════════════════════════════════════════════════════════
# MODEL INFERENCE
# ════════════════════════════════════════════════════════════
def analyze_email_model(subject: str, body: str):
    """Chạy DistilBERT. Trả về (is_phishing, confidence)."""
    if not (email_model and email_tokenizer):
        return False, 0.0
    try:
        text   = f"Subject: {subject}. Content: {body}"
        inputs = email_tokenizer(
            text, truncation=True, padding=True,
            max_length=512, return_tensors="pt"
        ).to(device)
        inputs.pop('token_type_ids', None)
        with torch.no_grad():
            probs = torch.nn.functional.softmax(
                email_model(**inputs).logits, dim=-1
            ).cpu().numpy()[0]
        idx = int(np.argmax(probs))
        return bool(idx == 1), round(float(probs[idx]), 4)
    except Exception as e:
        print(f"⚠️  Email model inference error: {e}")
        return False, 0.0


def analyze_url_model(url: str):
    """Chạy Random Forest. Trả về (is_phishing, confidence)."""
    if not _rf_deps_ok or rf_model is None or rf_features is None:
        return False, 0.0
    try:
        feats = _extract_url_features(url)
        X     = pd.DataFrame([feats])[rf_features]
        prob  = float(rf_model.predict_proba(X)[0][1])
        return prob >= rf_threshold, round(prob, 4)
    except Exception as e:
        print(f"⚠️  URL model inference error: {e}")
        return False, 0.0


def extract_urls(text: str) -> list:
    """Trích xuất HTTP(S) URL từ nội dung email."""
    href_urls  = re.findall(r'href=["\']?(https?://[^"\'>\s]+)', text, re.IGNORECASE)
    plain_urls = re.findall(r'(https?://[^\s<>"\']+)', text)
    seen, result = set(), []
    for u in href_urls + plain_urls:
        u = u.rstrip('.,;)')
        if u not in seen:
            seen.add(u)
            result.append(u)
    skip_ext = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.xml', '.css', 'xhtml')
    return [u for u in result if not any(u.lower().endswith(e) or e in u for e in skip_ext)]


# ════════════════════════════════════════════════════════════
# API ENDPOINTS
# ════════════════════════════════════════════════════════════
@app.get("/health")
async def health():
    return {
        "status":      "OK",
        "email_model": "loaded" if email_model else "not loaded",
        "url_model":   f"RF loaded (threshold={rf_threshold})" if rf_model else "not loaded",
    }


@app.post("/predict-eml")
async def predict_eml(file: UploadFile = File(...)):
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="Only .eml files allowed")

    try:
        raw  = await file.read()
        msg  = BytesParser(policy=policy.default).parsebytes(raw)
        subj = msg.get('subject') or "No Subject"

        def _get_body(msg_obj):
            if msg_obj.is_multipart():
                parts = []
                for part in msg_obj.walk():
                    ct = part.get_content_type()
                    cd = str(part.get('Content-Disposition', ''))
                    if ct in ('text/plain', 'text/html') and 'attachment' not in cd:
                        payload = part.get_payload(decode=True)
                        if payload is not None:
                            parts.append(payload.decode(errors='ignore'))
                return '\n'.join(parts)
            else:
                payload = msg_obj.get_payload(decode=True)
                if isinstance(payload, bytes):
                    return payload.decode(errors='ignore')
                return str(payload) if payload else ""

        body = _get_body(msg)

        # Phân tích email bằng model
        is_phish_email, email_conf = analyze_email_model(subj, body)

        # Phân tích từng URL bằng model
        urls            = extract_urls(body)
        url_results     = []
        suspicious_urls = []

        for url in urls:
            is_phish_url, url_conf = analyze_url_model(url)
            url_obj = {
                "url":         url,
                "is_phishing": is_phish_url,
                "confidence":  url_conf,
            }
            url_results.append(url_obj)
            if is_phish_url:
                suspicious_urls.append(url_obj)

        # final_verdict: DANGEROUS nếu email model HOẶC bất kỳ URL nào phishing
        final_verdict = "DANGEROUS" if (is_phish_email or any(u["is_phishing"] for u in url_results)) else "SAFE"

        safe_urls = [u for u in url_results if not u["is_phishing"]]

        return {
            "filename":      file.filename,
            "final_verdict": final_verdict,
            "email_details": {
                "is_phishing":   is_phish_email,
                "confidence":    email_conf,
                "ai_confidence": email_conf,
            },
            "url_analysis": {
                "total_urls":            len(url_results),
                "urls":                  [u["url"] for u in url_results],
                "safe_urls":             safe_urls,
                "suspicious_urls_found": suspicious_urls,
            },
        }

    except Exception as e:
        print(f"Error in /predict-eml: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict-url")
async def predict_url(payload: dict):
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")
    is_phishing, confidence = analyze_url_model(url)
    features = _extract_url_features(url) if _rf_deps_ok else {}
    return {
        "url":         url,
        "is_phishing": is_phishing,
        "confidence":  confidence,
        "features":    features,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)