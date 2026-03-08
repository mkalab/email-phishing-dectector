from fastapi import FastAPI, UploadFile, File, HTTPException
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
import mailparser
import re
import uvicorn
import os
import requests
import base64

app = FastAPI(title="🛡️ AI Phishing Shield (Hierarchical Defense)")

# --- CẤU HÌNH ---
VT_API_KEY = "a51201a756c4b0a0bc7e5c93b7912827964db0cc07f9533a80d9d233f1e91bc0" # se dung env sau
SUSPICIOUS_KEYWORDS = ['bit.ly', 't.co', 'tinyurl', 'login-verify', 'secure-update', 'account-alert', 'verify', 'banking', 'update-account']
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
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

# --- CÁC HÀM BỔ TRỢ ---

def check_with_keywords(url):
    return any(key in url.lower() for key in SUSPICIOUS_KEYWORDS)

def check_with_virustotal(url):
    """Kiểm tra URL bằng VirusTotal API"""
    try:
        url_id = base64.urlsafe_b64encode(url.encode()).decode().strip("=")
        endpoint = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        headers = {"x-apikey": VT_API_KEY}
        response = requests.get(endpoint, headers=headers, timeout=5)
        if response.status_code == 200:
            stats = response.json()['data']['attributes']['last_analysis_stats']
            is_malicious = (stats['malicious'] + stats['phishing']) > 0
            return is_malicious, True 
    except:
        pass
    return False, False # Thất bại (hết lượt hoặc lỗi mạng)

def analyze_url_hierarchical(url):
    # LỚP 1: URL AI MODEL
    if url_model and url_tokenizer:
        try:
            inputs = url_tokenizer(url, truncation=True, padding=True, max_length=128, return_tensors="pt").to(device)
            # DistilBERT doesn't use token_type_ids; remove if present
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            with torch.no_grad():
                outputs = url_model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1).cpu().numpy()[0]
            if np.argmax(probs) == 1: # Phishing
                return True, "url_ai_model"
            # Nếu AI bảo an toàn, vẫn trả về để ghi nhận phương thức
            return False, "url_ai_model"
        except Exception as e:
            print(f" URL Model failed for {url}, falling back... Error: {e}")

    # LỚP 2: VIRUSTOTAL 
    is_malicious_vt, success = check_with_virustotal(url)
    if success:
        return is_malicious_vt, "virustotal"

    # LỚP 3: KEYWORDS 
    return check_with_keywords(url), "keywords_fallback"

def extract_urls(text):
    # Lọc bỏ các URL rác như xml, xhtml để tránh AI báo nhầm
    urls = re.findall(r'(https?://[^\s<>"]+|www\.[^\s<>"]+)', text)
    return [u for u in urls if not any(ext in u for ext in ['.png', '.jpg', '.xml', 'xhtml'])]

# --- API ENDPOINTS ---

@app.post("/predict")
async def predict(payload: dict):
    """Simple text classifier used by the browser extension and Node frontend."""
    subject = payload.get("subject", "")
    body = payload.get("content", "")

    try:
        combined_text = f"Subject: {subject}. Content: {body}"
        is_ai_phishing = False
        ai_confidence = 0.0
        
        if email_model:
            inputs = email_tokenizer(combined_text, truncation=True, padding=True, max_length=128, return_tensors="pt").to(device)
            # DistilBERT doesn't use token_type_ids; remove if present
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            with torch.no_grad():
                outputs = email_model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1).cpu().numpy()[0]
            predicted_class = np.argmax(probs)
            is_ai_phishing = bool(predicted_class == 1)
            ai_confidence = round(float(probs[predicted_class]), 4)
        
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
        # --- BƯỚC 1: ĐỌC VÀ PHÂN TÍCH FILE EML ---
        raw_content = await file.read()
        mail = mailparser.parse_from_bytes(raw_content)
        subject = mail.subject or "No Subject"
        body = mail.body or ""
        
        # --- BƯỚC 2: TÁCH URL (TRƯỚC KHI CHẠY MODEL) ---
        urls = extract_urls(body)
        
        # --- BƯỚC 3: CHẠY EMAIL AI MODEL (KIỂM TRA NỘI DUNG) ---
        combined_text = f"Subject: {subject}. Content: {body}"
        is_ai_phishing = False
        ai_confidence = 0.0
        
        if email_model:
            inputs = email_tokenizer(combined_text, truncation=True, padding=True, max_length=128, return_tensors="pt").to(device)
            # DistilBERT doesn't use token_type_ids; remove if present
            if 'token_type_ids' in inputs:
                del inputs['token_type_ids']
            with torch.no_grad():
                outputs = email_model(**inputs)
                probs = torch.nn.functional.softmax(outputs.logits, dim=-1).cpu().numpy()[0]
            predicted_class = np.argmax(probs)
            is_ai_phishing = bool(predicted_class == 1)
            ai_confidence = round(float(probs[predicted_class]), 4)

        # --- BƯỚC 4: CHẠY URL MODEL & FALLBACK TRÊN DANH SÁCH URL ĐÃ TÁCH ---
        suspicious_urls = []
        methods_used = []

        for url in urls[:5]: # Kiểm tra tối đa 5 link để đảm bảo hiệu năng
            is_bad, method = analyze_url_hierarchical(url)
            methods_used.append(method)
            if is_bad:
                suspicious_urls.append({"url": url, "method": method})

        # --- BƯỚC 5: TỔNG HỢP KẾT QUẢ CUỐI CÙNG ---
        final_verdict = "SAFE"
        if is_ai_phishing or len(suspicious_urls) > 0:
            final_verdict = "DANGEROUS"

        return {
            "filename": file.filename,
            "analysis": {
                "email_content_ai": "PHISHING" if is_ai_phishing else "NORMAL",
                "ai_confidence": ai_confidence,
                "urls_extracted": urls, # Hiển thị các URL đã tách được
                "suspicious_urls_found": suspicious_urls,
                "url_check_methods": list(set(methods_used)) # Các phương thức đã dùng
            },
            "final_verdict": final_verdict
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict-url")
async def predict_url(payload: dict):
    url = payload.get("url")
    if not url: raise HTTPException(status_code=400, detail="Missing URL")
    is_bad, method = analyze_url_hierarchical(url)
    return {"url": url, "is_phishing": is_bad, "method_used": method}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)