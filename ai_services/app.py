from fastapi import FastAPI, UploadFile, File, HTTPException
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import email
from email.policy import default
import re, math, json
import uvicorn
import os

# ── [THÊM MỚI] Import cho Random Forest URL model ─────────────
import joblib
import pandas as pd
import tldextract

app = FastAPI(title="AI Phishing Shield")

# ── CẤU HÌNH ──────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
device   = "cuda" if torch.cuda.is_available() else "cpu"

# =============================================================
# LOAD EMAIL MODEL (HuggingFace — giữ nguyên)
# =============================================================
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

# =============================================================
# LOAD URL MODEL (scikit-learn Random Forest — joblib)
# Model được train bằng pipeline RF mới, lưu dưới dạng .joblib.
# =============================================================
URL_MODEL_PATH  = os.path.join(BASE_DIR, "url_phishing_classifier_final")
url_rf_model    = None   # RandomForestClassifier
url_feature_names = None # list tên feature
url_threshold   = 0.5    # default, sẽ bị ghi đè bởi config.json

try:
    url_rf_model      = joblib.load(os.path.join(URL_MODEL_PATH, "rf_model.joblib"))
    url_feature_names = joblib.load(os.path.join(URL_MODEL_PATH, "feature_names.joblib"))

    # Đọc optimal threshold đã lưu khi train
    config_path = os.path.join(URL_MODEL_PATH, "config.json")
    if os.path.exists(config_path):
        with open(config_path) as f:
            cfg = json.load(f)
        url_threshold = cfg.get("optimal_threshold", 0.5)

    print(f"✅ URL RF model loaded  |  features={len(url_feature_names)}  |  threshold={url_threshold}")
except Exception as e:
    print(f"⚠️  URL model error: {e}")


SUSPICIOUS_WORDS = [
    'login', 'signin', 'logon', 'verify', 'verification', 'secure', 'security',
    'account', 'update', 'confirm', 'validation', 'authenticate', 'auth',
    'bank', 'banking', 'payment', 'pay', 'invoice', 'billing', 'transaction',
    'credit', 'debit', 'card', 'visa', 'mastercard', 'wallet', 'crypto', 'btc', 'eth',
    'urgent', 'immediately', 'asap', 'alert', 'warning', 'notice', 'important',
    'suspend', 'suspension', 'limited', 'expire', 'expired', 'deadline', 'locked',
    'free', 'prize', 'winner', 'win', 'gift', 'bonus', 'reward', 'claim', 'offer',
    'promotion', 'promo', 'discount', 'deal',
    'click', 'clicking', 'access', 'open', 'download', 'install', 'view', 'submit',
    'enter', 'continue', 'proceed',
    'password', 'passcode', 'pin', 'otp', 'credential', 'username', 'id', 'identity',
    'support', 'helpdesk', 'service', 'customer', 'care', 'admin', 'team',
    'notification', 'message', 'mail', 'inbox', 'delivery', 'tracking',
    'securelogin', 'accountverify', 'webscr', 'loginsecure', 'securitycheck',
]

TRUSTED_BRANDS = [
    'google', 'apple', 'microsoft', 'amazon', 'facebook', 'meta', 'instagram',
    'whatsapp', 'youtube', 'twitter', 'x', 'linkedin', 'snapchat', 'tiktok',
    'paypal', 'stripe', 'square', 'payoneer', 'skrill', 'wise', 'revolut',
    'visa', 'mastercard', 'americanexpress', 'amex',
    'chase', 'bankofamerica', 'wellsfargo', 'citibank', 'hsbc', 'barclays',
    'binance', 'coinbase', 'kraken', 'metamask', 'trustwallet', 'blockchain',
    'ebay', 'shopify', 'alibaba', 'aliexpress', 'etsy', 'rakuten',
    'github', 'gitlab', 'bitbucket', 'aws', 'azure', 'gcp', 'cloudflare',
    'steam', 'epicgames', 'riotgames', 'playstation', 'xbox', 'nintendo',
    'gmail', 'outlook', 'yahoo', 'protonmail', 'icloud', 'zoho',
    'fedex', 'dhl', 'ups', 'usps',
    'vietcombank', 'techcombank', 'mbbank', 'acb', 'vpbank',
    'momo', 'zalopay', 'shopee', 'lazada', 'tiki',
]


def _calc_entropy(s: str) -> float:
    """Shannon entropy — domain ngẫu nhiên (phishing) có entropy cao hơn."""
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((cnt / n) * math.log2(cnt / n) for cnt in freq.values())


def _edit_distance(a: str, b: str) -> int:
    """
    Khoảng cách Levenshtein giữa hai chuỗi (không dùng thư viện ngoài).
    Dùng DP O(m×n) — đủ nhanh cho domain string ngắn.
    """
    m, n = len(a), len(b)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev, dp[0] = dp[0], i
        for j in range(1, n + 1):
            temp = dp[j]
            if a[i - 1] == b[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = temp
    return dp[n]


# Bảng chuẩn hoá leet-speak / homoglyph ASCII
_LEET_MAP = str.maketrans({
    '0': 'o', '1': 'l', '2': 'z', '3': 'e',
    '4': 'a', '5': 's', '6': 'g', '7': 't',
    '8': 'b', '9': 'g', '@': 'a', '$': 's',
})


def _normalize_domain(s: str) -> str:
    """Chuẩn hoá domain về dạng alphabetic để detect typosquatting."""
    return s.lower().translate(_LEET_MAP)


def _has_typo_brand(domain: str, brands: list, max_dist: int = 2) -> bool:
    """Kiểm tra domain có phải biến thể typo của một brand nổi tiếng không."""
    dom_lower = domain.lower()
    norm      = _normalize_domain(domain)
    for brand in brands:
        if len(brand) < 5:          # Brand quá ngắn → dễ false positive
            continue
        if dom_lower == brand:      # Domain THẬT khớp chính xác → bỏ qua
            continue                # (giữ 'paypa1' → norm='paypal' vẫn được flag)
        if _edit_distance(norm, brand) <= max_dist:
            return True
    return False


def extract_features(url: str) -> dict:
    """
    ⚠️  PHẢI KHỚP 100% VỚI extract_features() TRONG TRAINING PIPELINE.
        Mọi thay đổi ở đây đòi hỏi train lại model.
    """
    url = str(url)
    try:
        ext = tldextract.extract(url)
        domain, suffix, subdomain = ext.domain, ext.suffix, ext.subdomain
    except Exception:
        domain = suffix = subdomain = ''

    path      = re.sub(r'https?://[^/]+', '', url)
    url_lower = url.lower()
    dom_lower = domain.lower()
    sub_lower = subdomain.lower()

    # ── [GỐC v2.0] 39 features — KHÔNG THAY ĐỔI ─────────────
    features = {
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
        'is_common_tld':         int(suffix in ['com', 'org', 'net', 'edu', 'gov']),
        'is_suspicious_tld':     int(suffix in ['tk', 'ml', 'ga', 'cf', 'gq', 'xyz', 'top', 'pw']),
        'suspicious_word_count': sum(1 for w in SUSPICIOUS_WORDS if w in url_lower),
        'has_login_word':        int(any(w in url_lower for w in ['login', 'signin', 'logon'])),
        'has_verify_word':       int(any(w in url_lower for w in ['verify', 'confirm', 'validate'])),
        'has_secure_word':       int('secure' in url_lower),
        'has_bank_word':         int(any(w in url_lower for w in ['bank', 'paypal', 'visa', 'mastercard'])),
        'num_tokens':            len(re.split(r'[/\-_?=&.]', url)),
        'max_token_length':      max((len(t) for t in re.split(r'[/\-_?=&.]', url) if t), default=0),
        'has_port':              int(bool(re.search(r':\d{2,5}[/\s]', url))),
        'double_slash_in_path':  int('//' in path),
        'url_depth':             len([p for p in path.split('/') if p]),
        'has_redirect':          int(url.count('http') > 1),
    }

    # ── [v2.0] Shannon entropy + long URL ────────────────────
    features['domain_entropy'] = round(_calc_entropy(domain), 4)
    features['is_long_url']    = int(len(url) > 75)

    # ── [v2.0→v3.0] Brand analysis — tách thành 3 signal riêng ──
    brand_in_url       = any(b in url_lower for b in TRUSTED_BRANDS)
    brand_in_domain    = any(b in dom_lower for b in TRUSTED_BRANDS)
    brand_in_subdomain = any(b in sub_lower for b in TRUSTED_BRANDS)

    features['brand_in_url']       = int(brand_in_url)
    features['brand_in_domain']    = int(brand_in_domain)
    features['brand_in_subdomain'] = int(brand_in_subdomain and not brand_in_domain)

    full_domain = (sub_lower + '.' + dom_lower)
    features['has_suspicious_brand'] = int(
        brand_in_url and not any(b in full_domain for b in TRUSTED_BRANDS)
    )

    # ── [v3.0] Typosquatting ──────────────────────────────────
    features['has_typo_brand'] = int(_has_typo_brand(domain, TRUSTED_BRANDS, max_dist=2))

    # ── [v3.0] Homograph / Unicode attack ────────────────────
    try:
        domain.encode('ascii')
        features['has_unicode_domain'] = 0
    except UnicodeEncodeError:
        features['has_unicode_domain'] = 1

    # ── [v3.0] Multiple domains / redirect ───────────────────
    features['multiple_domains'] = int(url.count('http') > 1)

    # ── [v3.0] Domain readability signals ────────────────────
    features['is_short_domain'] = int(len(domain) <= 3)

    consonants = set('bcdfghjklmnpqrstvwxyz')
    dom_alpha  = [c for c in dom_lower if c.isalpha()]
    features['consonant_ratio'] = round(
        sum(1 for c in dom_alpha if c in consonants) / max(len(dom_alpha), 1), 4
    )

    features['digit_sequence'] = int(bool(re.search(r'\d{3,}', domain)))

    return features


def analyze_email_model(subject: str, body: str):
    if email_model and email_tokenizer:
        try:
            combined_text = f"Subject: {subject}. Content: {body}"
            inputs = email_tokenizer(
                combined_text, truncation=True, padding=True,
                max_length=128, return_tensors="pt"
            ).to(device)
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            with torch.no_grad():
                outputs = email_model(**inputs)
                probs   = torch.nn.functional.softmax(outputs.logits, dim=-1).cpu().numpy()[0]
            predicted_class = np.argmax(probs)
            return bool(predicted_class == 1), round(float(probs[predicted_class]), 4)
        except Exception as e:
            print(f"⚠️  Email model failed: {e}")
    return False, 0.0


def analyze_url_model(url: str):
    """
    Classify URL bằng Random Forest đã train.
    Dùng optimal threshold lấy từ config.json thay vì hardcode 0.5.
    """
    if url_rf_model is None or url_feature_names is None:
        return False, 0.0
    try:
        feats = extract_features(url)
        # Tạo DataFrame với đúng thứ tự cột như lúc train
        X = pd.DataFrame([feats])[url_feature_names]
        prob        = float(url_rf_model.predict_proba(X)[0][1])
        is_phishing = prob >= url_threshold
        return bool(is_phishing), round(prob, 4)
    except Exception as e:
        print(f"⚠️  URL RF model failed for {url}: {e}")
        return False, 0.0


def extract_urls(text: str) -> list:
    href_urls  = re.findall(r'href=["\']?(https?://[^"\'>\s]+)', text, re.IGNORECASE)
    plain_urls = re.findall(r'(https?://[^\s<>"\']+)', text)
    seen, all_urls = set(), []
    for u in href_urls + plain_urls:
        u = u.rstrip('.,;)')
        if u not in seen:
            seen.add(u)
            all_urls.append(u)
    SKIP_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.xml', '.css', 'xhtml')
    return [u for u in all_urls if not any(u.lower().endswith(e) or e in u for e in SKIP_EXT)]



@app.get("/health")
async def health():
    return {
        "status":        "OK",
        "email_model":   "loaded" if email_model else "not loaded",
        "url_rf_model":  "loaded" if url_rf_model else "not loaded",
        "url_threshold": url_threshold,
    }


@app.post("/predict")
async def predict(payload: dict):
    """Phân tích email dạng text — dùng bởi extension và Node frontend."""
    subject = payload.get("subject", "")
    body    = payload.get("content", "")
    try:
        is_ai_phishing, ai_confidence = analyze_email_model(subject, body)
        return {
            "analysis": {
                "email_content_ai":     "PHISHING" if is_ai_phishing else "NORMAL",
                "ai_confidence":        ai_confidence,
                "urls_extracted":       [],
                "suspicious_urls_found": [],
                "url_check_methods":    [],
            },
            "final_verdict": "DANGEROUS" if is_ai_phishing else "SAFE",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict-eml")
async def predict_eml(file: UploadFile = File(...)):
    """Phân tích file .eml — email model + RF URL model."""
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="Only .eml files allowed")
    try:
        raw_content = await file.read()
        msg         = email.message_from_bytes(raw_content, policy=default)
        subject     = msg.get('subject') or "No Subject"

        if msg.is_multipart():
            body = '\n'.join(
                part.get_payload(decode=True).decode(errors='ignore')
                for part in msg.get_payload()
                if part.get_content_type().startswith('text/')
            )
        else:
            payload_ = msg.get_payload(decode=True)
            body     = payload_.decode(errors='ignore') if isinstance(payload_, bytes) else (payload_ or "")

        urls = extract_urls(body)
        is_ai_phishing, ai_confidence = analyze_email_model(subject, body)

        suspicious_urls = []
        for url in urls[:5]:
            is_phishing, confidence = analyze_url_model(url)
            if is_phishing:
                suspicious_urls.append({"url": url, "confidence": confidence})

        final_verdict = "DANGEROUS" if (is_ai_phishing or suspicious_urls) else "SAFE"

        return {
            "filename": file.filename,
            "analysis": {
                "email_content_ai":      "PHISHING" if is_ai_phishing else "NORMAL",
                "ai_confidence":         ai_confidence,
                "all_urls_found":        urls,
                "total_urls_found":      len(urls),
                "suspicious_urls_found": suspicious_urls,
            },
            "final_verdict": final_verdict,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict-url")
async def predict_url(payload: dict):
    """Phân tích một URL đơn lẻ."""
    url = payload.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="Missing URL")
    is_phishing, confidence = analyze_url_model(url)
    return {"url": url, "is_phishing": is_phishing, "confidence": confidence}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)