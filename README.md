# Email Phishing Service

This repository contains an AI-based phishing detection backend implemented
with FastAPI. It loads pretrained Transformers models to classify email
content and URLs.

## Setup

1. Create a virtual environment (Python 3.11+ recommended):
   ```bash
   python -m venv venv
   source venv/Scripts/activate        # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` file permits either NumPy 1.x or 2.x. **If you
   intend to use NumPy 2.x**, you must ensure that all dependent packages
   that include compiled extensions (PyTorch, torchvision, TensorFlow,
   etc.) are themselves built against the NumPy 2 C API. Otherwise the
   process will crash with errors like `_ARRAY_API not found`.

## Running the Entire Project

The project consists of three main components:

### 1. AI Service (Python FastAPI)
- **Purpose**: Core ML inference for email and URL classification.
- **Port**: 8000
- **Run**:
  ```bash
  cd ai_services
  python app.py
  ```

### 2. Node.js Backend
- **Purpose**: Web server with UI and API proxy to Python service.
- **Port**: 3000
- **Setup**:
  ```bash
  cd web_backend
  npm install
  npm start
  ```
- **Web UI**: Visit http://localhost:3000 to upload .eml files.

### 3. Browser Extension (Chrome)
- **Purpose**: Integrates phishing detection into Gmail.
- **Install**:
  1. Open Chrome and go to `chrome://extensions/`
  2. Enable "Developer mode" (top right)
  3. Click "Load unpacked" and select the `phishing_extension/` folder
  4. The extension will appear in your extensions list
- **Usage**: 
  - **In Gmail**: Click the "🛡️ Scan with AI" button on emails.
  - **In Extension Popup**: Switch between "Quét Email" (upload .eml) and "Quét URL" (enter URL directly).

### Quick Start (All Services)
Use the provided batch script to start everything:
```bash
run_project.bat
```
This will:
- Stop any existing processes
- Start the Python AI service
- Start the temporary Python UI (for testing)
- Start the Node.js backend

### Manual Startup Order
1. Start AI Service: `python ai_services/app.py`
2. Start Node.js: `cd web_backend && npm start`
3. (Optional) Start Test UI: `python ai_services/ui.py` (runs on port 8001)

### Health Checks
- AI Service: http://localhost:8000/docs (FastAPI docs)
- Node.js Backend: http://localhost:3000/health
- AI Health via Node: http://localhost:3000/api/health-ai

## Running with NumPy 2.x

To migrate the environment for NumPy 2.0:

1. Upgrade or reinstall packages that depend on NumPy using compatible
   versions. Many projects are still rolling out wheels for NumPy 2; if
   a wheel isn't available you can build from source:
   ```bash
   pip install --force-reinstall --no-binary :all: torch torchvision
   pip install --force-reinstall --no-binary :all: tensorflow
   # rebuild any other packages that ship extensions
   ```
   Make sure the build uses `pybind11>=2.12` or newer; earlier versions do
   not compile the required API.

2. Verify the build succeeded by starting Python and importing the
   packages when NumPy 2 is installed:
   ```python
   import numpy; print(numpy.__version__)
   import torch  # should import without _ARRAY_API errors
   import tensorflow
   ```

3. When running `ai_services/app.py`, a warning will be printed if
   NumPy 2 is detected. This does **not** stop the server; it just
   reminds you that the onus is on you to rebuild the underlying
   extensions.

   Example log line:
   ```
   ⚠️ Running under numpy >=2.0 – make sure all dependent extensions are built with NumPy 2 support (pybind11>=2.12, rebuild torch/tensorflow/etc.).
   ```

3. If any module still fails, downgrading to `numpy<2` is the quickest
   workaround until the dependency releases a compatible build.

## API Endpoints

The Python service exposes the following POST endpoints:

* `/predict` – classify arbitrary email text. Accepts JSON with
  `subject` and `content` fields; used by the Node frontend and browser
  extension.
* `/predict-eml` – upload an `.eml` file; returns analysis of the message
  and any URLs it contains.
* `/predict-url` – classify a single URL (used internally by the service).

The Node.js backend proxies these with additional endpoints:

* `/api/analyze-text` – proxy to `/predict` for text classification.
* `/api/analyze-file` – proxy to `/predict-eml` for file uploads.
* `/api/analyze-url` – proxy to `/predict-url` for URL classification.

All endpoints return JSON with an `analysis` object and `final_verdict`.


## Troubleshooting

* **Import errors mentioning `_ARRAY_API` or incompatible NumPy versions:**
  see the migration instructions above.

* **Model loading errors** will print to stdout during startup; the
  server continues running in degraded mode and any prediction endpoint
  will raise an HTTP 500 when the model isn't available.

## License

[Add license information here if applicable.]
