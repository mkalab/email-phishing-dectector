from fastapi import FastAPI, UploadFile, File, HTTPException
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import email
from email.policy import default
import re
import uvicorn
import os

app = FastAPI(title="AI Phishing Shield")

# --- CẤU HÌNH ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cuda" if torch.cuda.is_available() else "cpu"

# --- TẢI MODEL AI ---

EMAIL_MODEL_PATH = os.path.join(BASE_DIR, "phishing_classifier_final")
email_tokenizer = None
email_model = None
try:
    email_tokenizer = AutoTokenizer.from_pretrained(EMAIL_MODEL_PATH, local_files_only=True)
    email_model = AutoModelForSequenceClassification.from_pretrained(EMAIL_MODEL_PATH, local_files_only=True)
    email_model.to(device).eval()
    print(f" Email model loaded on {device}")
except Exception as e:
    print(f" Email model error: {e}")

URL_MODEL_PATH = os.path.join(BASE_DIR, "url_phishing_classifier_final")
url_tokenizer = None
url_model = None
try:
    url_tokenizer = AutoTokenizer.from_pretrained(URL_MODEL_PATH, local_files_only=True)
    url_model = AutoModelForSequenceClassification.from_pretrained(URL_MODEL_PATH, local_files_only=True)
    url_model.to(device).eval()
    print(f" URL model loaded on {device}")
except Exception as e:
    print(f" URL model error: {e}")


def analyze_email_model(subject, body):
    """Analyze email content using AI model only"""
    if email_model and email_tokenizer:
        try:
            combined_text = f"Subject: {subject}. Content: {body}"
            inputs = email_tokenizer(combined_text, truncation=True, padding=True, max_length=128, return_tensors="pt").to(device)
            # DistilBERT doesn't use token_type_ids; remove if present
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            with torch.no_grad():
                outputs = email_model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1).cpu().numpy()[0]
            predicted_class = np.argmax(probs)
            is_phishing = bool(predicted_class == 1)
            confidence = round(float(probs[predicted_class]), 4)
            return is_phishing, confidence
        except Exception as e:
            print(f" Email Model failed. Error: {e}")
            return False, 0.0
    return False, 0.0

def analyze_url_model(url):
    """Analyze URL using AI model only"""
    if url_model and url_tokenizer:
        try:
            inputs = url_tokenizer(url, truncation=True, padding=True, max_length=128, return_tensors="pt").to(device)
            # DistilBERT doesn't use token_type_ids; remove if present
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            with torch.no_grad():
                outputs = url_model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1).cpu().numpy()[0]
            is_phishing = bool(np.argmax(probs) == 1)
            confidence = round(float(probs[np.argmax(probs)]), 4)
            return is_phishing, confidence
        except Exception as e:
            print(f" URL Model failed for {url}. Error: {e}")
            return False, 0.0
    return False, 0.0

def extract_urls(text):
    # 1. Ưu tiên lấy URL từ href="..." trong HTML email (bắt được <a href="https://...">)
    href_urls = re.findall(r'href=["\']?(https?://[^"\'>\s]+)', text, re.IGNORECASE)
    # 2. Lấy URL plain text trong nội dung
    plain_urls = re.findall(r'(https?://[^\s<>"\']+)', text)
    # Gộp lại, giữ thứ tự, loại trùng
    seen = set()
    all_urls = []
    for u in href_urls + plain_urls:
        # Bỏ dấu chấm/ngoặc thừa ở cuối URL
        u = u.rstrip('.,;)')
        if u not in seen:
            seen.add(u)
            all_urls.append(u)
    # Loại bỏ URL tài nguyên tĩnh không cần quét
    SKIP_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.xml', '.css', 'xhtml')
    return [u for u in all_urls if not any(u.lower().endswith(ext) or ext in u for ext in SKIP_EXT)]

# --- API ENDPOINTS ---

@app.post("/predict")
async def predict(payload: dict):
    """Simple text classifier used by the browser extension and Node frontend."""
    subject = payload.get("subject", "")
    body = payload.get("content", "")

    try:
        is_ai_phishing, ai_confidence = analyze_email_model(subject, body)
        
        final_verdict = "DANGEROUS" if is_ai_phishing else "SAFE"
        return {
            "analysis": {
                "email_content_ai": "PHISHING" if is_ai_phishing else "NORMAL",
                "ai_confidence": ai_confidence,
                # For the simple endpoint we don't scan URLs, but keep keys for
                # compatibility with the existing frontend responses.
                "urls_extracted": [],
                "suspicious_urls_found": [],
                "url_check_methods": []
            },
            "final_verdict": final_verdict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-eml")
async def predict_eml(file: UploadFile = File(...)):
    if not file.filename.endswith('.eml'):
        raise HTTPException(status_code=400, detail="Only .eml files allowed")

    try:

        raw_content = await file.read()
        msg = email.message_from_bytes(raw_content, policy=default)
        subject = msg.get('subject') or "No Subject"
        
        # Extract body
        if msg.is_multipart():
            body = '\n'.join(
                part.get_payload(decode=True).decode(errors='ignore')
                for part in msg.get_payload()
                if part.get_content_type().startswith('text/')
            )
        else:
            payload = msg.get_payload(decode=True)
            body = payload.decode(errors='ignore') if isinstance(payload, bytes) else (payload or "")
        
        urls = extract_urls(body)
        
        is_ai_phishing, ai_confidence = analyze_email_model(subject, body)

        suspicious_urls = []
        for url in urls[:5]:
            is_phishing, confidence = analyze_url_model(url)
            if is_phishing:
                suspicious_urls.append({"url": url, "confidence": confidence})

        final_verdict = "SAFE"
        if is_ai_phishing or len(suspicious_urls) > 0:
            final_verdict = "DANGEROUS"

        return {
            "filename": file.filename,
            "analysis": {
                "email_content_ai": "PHISHING" if is_ai_phishing else "NORMAL",
                "ai_confidence": ai_confidence,
                "all_urls_found": urls,
                "total_urls_found": len(urls),
                "suspicious_urls_found": suspicious_urls
            },
            "final_verdict": final_verdict
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-url")
async def predict_url(payload: dict):
    url = payload.get("url")
    if not url: raise HTTPException(status_code=400, detail="Missing URL")
    is_phishing, confidence = analyze_url_model(url)
    return {"url": url, "is_phishing": is_phishing, "confidence": confidence}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)