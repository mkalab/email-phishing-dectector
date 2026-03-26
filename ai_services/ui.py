from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
import requests
import json

app = FastAPI(title="🛠️ Phishing Shield UI")

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Phishing Shield Test UI</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        .result { background: #f4f4f4; padding: 1em; border-radius: 8px; margin-top: 1em; white-space: pre-wrap; }
        .section { margin-bottom: 2em; }
        hr { margin: 2em 0; }
        .feature { margin-left: 2em; font-family: monospace; }
    </style>
</head>
<body>
    <h1>🛡️ AI Phishing Shield - Test Interface</h1>
    <div class="section">
        <h2>📧 Upload .eml file</h2>
        <form action="/submit-eml" enctype="multipart/form-data" method="post">
            <input type="file" name="file" accept=".eml" required />
            <input type="submit" value="Analyze Email" />
        </form>
    </div>
    <div class="section">
        <h2>🔗 Check URL</h2>
        <form action="/submit-url" method="post">
            <input type="text" name="url" placeholder="https://example.com" required />
            <input type="submit" value="Analyze URL" />
        </form>
    </div>
</body>
</html>
"""

def render_json_as_lines(data, indent=0):
    """Đệ quy để hiển thị JSON dạng key: value trên từng dòng"""
    lines = []
    prefix = "  " * indent
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.extend(render_json_as_lines(v, indent+1))
            else:
                lines.append(f"{prefix}{k}: {v}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            lines.append(f"{prefix}[{i}]:")
            lines.extend(render_json_as_lines(item, indent+1))
    else:
        lines.append(f"{prefix}{data}")
    return lines

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE

@app.post("/submit-eml", response_class=HTMLResponse)
async def submit_eml(file: UploadFile = File(...)):
    content = await file.read()
    files = {"file": (file.filename, content, "message/rfc822")}
    try:
        resp = requests.post("http://127.0.0.1:8000/predict-eml", files=files)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {e}")
    except ValueError:
        return HTMLResponse(f"<pre>Backend returned non-JSON:\n{resp.text}</pre>")

    # Render JSON thành dòng
    lines = render_json_as_lines(data)
    html = f"<h2>📄 Analysis Result for {file.filename}</h2><div class='result'>" + "<br>".join(lines) + "</div>"
    return HTMLResponse(html)

@app.post("/submit-url", response_class=HTMLResponse)
async def submit_url(url: str = Form(...)):
    try:
        resp = requests.post("http://127.0.0.1:8000/predict-url", json={"url": url})
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Backend error: {e}")
    except ValueError:
        return HTMLResponse(f"<pre>Backend returned non-JSON:\n{resp.text}</pre>")

    lines = render_json_as_lines(data)
    html = f"<h2>🔍 URL Analysis Result</h2><div class='result'>" + "<br>".join(lines) + "</div>"
    return HTMLResponse(html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8100)