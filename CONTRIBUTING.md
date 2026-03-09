# Contributing to Email Phishing Detection Project

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 16+
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd email-phishing-detection
   ```

2. **Setup Python environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Setup AI Models**
   ```bash
   # Option 1: Download real models (recommended for production)
   python setup_models.py --all

   # Option 2: Create mock models (for development/testing only)
   python setup_models.py --all --mock

   # Option 3: Interactive setup
   python setup_models.py
   ```

4. **Setup Node.js backend**
   ```bash
   cd web_backend
   npm install
   cd ..
   ```

5. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

## 🤖 Model Setup

The project uses AI models that are not included in the git repository due to size and licensing considerations. You have several options:

### Option 1: Download Real Models (Recommended)
```bash
python setup_models.py --all
```
This downloads the actual trained models from HuggingFace Hub.

### Option 2: Create Mock Models (Development Only)
```bash
python setup_models.py --all --mock
```
Creates lightweight mock models for development and testing. **⚠️ Not suitable for production use.**

### Option 3: Manual Setup
If you have access to the trained models:
1. Place email model files in `ai_services/phishing_classifier_final/`
2. Place URL model files in `ai_services/url_phishing_classifier_final/`
3. Ensure the directory structure matches the expected format

### Model Files Structure
```
ai_services/
├── phishing_classifier_final/     # Email classification model
│   ├── config.json
│   ├── pytorch_model.bin (or model.safetensors)
│   ├── tokenizer_config.json
│   ├── vocab.txt
│   └── ...
└── url_phishing_classifier_final/ # URL classification model
    ├── config.json
    ├── pytorch_model.bin (or model.safetensors)
    ├── tokenizer_config.json
    ├── vocab.txt
    └── ...
```

### Troubleshooting Model Issues
- **Model loading errors**: Check that model files are in correct directories
- **Out of memory**: Use smaller models or reduce batch sizes
- **Network issues**: Models may take time to download on slow connections

5. **Download/Setup AI models**
   - Models are not included in git for security reasons
   - Download pre-trained models from HuggingFace or train locally
   - Place in `ai_services/phishing_classifier_final/` and `ai_services/url_phishing_classifier_final/`

## 🛠️ Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Changes
- Follow the existing code style
- Add tests for new features
- Update documentation
- Ensure all tests pass

### 3. Commit Changes
```bash
git add .
git commit -m "feat: add new phishing detection algorithm

- Added ML-based URL analysis
- Improved accuracy by 15%
- Added unit tests"
```

### 4. Push and Create Pull Request
```bash
git push origin feature/your-feature-name
# Create PR on GitHub
```

## 📝 Code Standards

### Python Code Style
- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters
- Use Black for formatting

### JavaScript Code Style
- Use ESLint configuration
- Follow Airbnb JavaScript Style Guide
- Use Prettier for formatting

### Commit Messages
Follow conventional commits:
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🧪 Testing

### Running Tests
```bash
# Python tests
cd ai_services
python -m pytest

# Node.js tests
cd web_backend
npm test
```

### Test Coverage
- Aim for 80%+ code coverage
- Include unit tests for all new features
- Add integration tests for API endpoints

## 📚 Documentation

### API Documentation
- Update FastAPI docs for new endpoints
- Document request/response formats
- Include examples

### Code Documentation
- Add docstrings to all functions
- Comment complex logic
- Update README.md for new features

## 🔒 Security Guidelines

### Before Committing
- [ ] No API keys or secrets in code
- [ ] Sensitive data is in .env (not committed)
- [ ] Model files are not committed
- [ ] Run security linter

### Code Review Checklist
- [ ] Security vulnerabilities checked
- [ ] No hardcoded secrets
- [ ] Input validation implemented
- [ ] Error handling added

## 🚀 Deployment

### Local Development
```bash
# Start all services
./run_project.bat  # Windows
# or manually:
python ai_services/app.py &
cd web_backend && npm start &
```

### Production Deployment
- Use Docker containers
- Configure environment variables
- Setup monitoring and logging
- Implement rate limiting

## 🤝 Communication

### Issues and Discussions
- Use GitHub Issues for bugs/features
- Use GitHub Discussions for questions
- Tag appropriate team members

### Code Reviews
- All PRs require at least 1 approval
- Review focuses on code quality, security, and functionality
- Be constructive and respectful

## 📋 Project Structure

```
email-phishing-detection/
├── ai_services/           # Python FastAPI backend
│   ├── app.py            # Main API application
│   ├── ui.py             # Development UI
│   └── phishing_classifier_final/  # Email model (not in git)
├── web_backend/          # Node.js Express server
│   ├── server.js         # Main server file
│   └── public/           # Static files
├── phishing_extension/   # Chrome extension
│   ├── manifest.json     # Extension manifest
│   ├── popup.html        # Extension popup
│   └── content.js        # Gmail integration
├── .env.example          # Environment template
├── .gitignore           # Git ignore rules
├── SECURITY.md          # Security guidelines
└── README.md            # Project documentation
```

## 🎯 Best Practices

### Git Best Practices
- Never commit directly to main/master
- Keep commits small and focused
- Write clear commit messages
- Rebase instead of merge when possible

### Code Quality
- Write self-documenting code
- Use meaningful variable names
- Keep functions small and focused
- Add error handling

### Performance
- Optimize model inference
- Implement caching where appropriate
- Monitor memory usage
- Profile performance bottlenecks

## 📞 Getting Help

- Check existing issues and documentation first
- Create detailed bug reports with reproduction steps
- Ask questions in GitHub Discussions
- Contact maintainers for urgent issues

## 🙏 Recognition

Contributors will be recognized in:
- README.md contributors section
- GitHub repository contributors
- Release notes

Thank you for contributing to making the internet safer! 🛡️

---

*Last updated: March 9, 2026*</content>
<parameter name="filePath">c:\EmailPhishing\Email Phishing\CONTRIBUTING.md