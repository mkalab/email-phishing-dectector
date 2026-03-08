from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
import requests

app = FastAPI(title="🛠️ Temporary UI for Phishing API")

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Phishing API Test UI</title>
</head>
<body>
    <h1>Phishing Shield Test Interface</h1>
    <h2>Upload .eml file</h2>
    <form action="/submit-eml" enctype="multipart/form-data" method="post">
        <input type="file" name="file" accept=".eml" required />
        <input type="submit" value="Analyze Email" />
    </form>
    <hr />
    <h2>Check URL</h2>
    <form action="/submit-url" method="post">
        <input type="text" name="url" placeholder="https://example.com" required />
        <input type="submit" value="Analyze URL" />
    </form>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE

@app.post("/submit-eml", response_class=HTMLResponse)
async def submit_eml(file: UploadFile = File(...)):
    content = await file.read()
    files = {"file": (file.filename, content, "message/rfc822")}
    try:
        resp = requests.post("http://127.0.0.1:8000/predict-eml", files=files)
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Backend unreachable: {e}")
    return HTMLResponse(f"<pre>{resp.text}</pre>")

@app.post("/submit-url", response_class=HTMLResponse)
async def submit_url(url: str = Form(...)):
    try:
        resp = requests.post("http://127.0.0.1:8000/predict-url", json={"url": url})
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Backend unreachable: {e}")
    return HTMLResponse(f"<pre>{resp.text}</pre>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8100)