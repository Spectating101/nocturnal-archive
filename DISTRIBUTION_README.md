# Cite-Agent Distribution Guide

## ✅ Ready for Distribution

### Available Packages

| Platform | File | Size | Status |
|----------|------|------|--------|
| **PyPI** | `cite_agent-1.0.0-py3-none-any.whl` | 166KB | ✅ Ready |
| **Source** | `cite_agent-1.0.0.tar.gz` | 207KB | ✅ Ready |
| **Linux Binary** | `cite-agent` (standalone) | 17MB | ✅ Ready |
| **Debian/Ubuntu** | `cite-agent_1.0.0_amd64.deb` | 17MB | ✅ Ready |
| **Windows** | `cite-agent-setup.exe` | - | ⏳ Requires Windows build |
| **macOS** | `cite-agent-1.0.0.dmg` | - | ⏳ Requires macOS build |

---

## 🚀 Quick Start for Users

### Option A: pip install (Developers)
```bash
pip install cite-agent
cite-agent --setup
```

### Option B: Debian/Ubuntu
```bash
sudo dpkg -i cite-agent_1.0.0_amd64.deb
cite-agent --setup
```

### Option C: Standalone Binary (Linux)
```bash
chmod +x cite-agent
./cite-agent --setup
```

---

## 🔒 Security Features Implemented

1. **Backend-only API keys** - Users never see or enter API keys
2. **JWT authentication** - 30-day tokens with secure refresh
3. **Binary compilation** - PyInstaller bundles code (harder to reverse engineer)
4. **Stripped binaries** - Debug symbols removed, compressed with UPX
5. **Server-side enforcement** - Rate limits, daily quotas (25,000 tokens/user)
6. **Excluded from distribution**:
   - Server code (`cite-agent-api/`)
   - Tests and docs
   - Development tools
   - Build artifacts

---

## 📦 Publishing to PyPI

### Test on PyPI Test Server
```bash
source build_env/bin/activate
twine upload --repository testpypi dist/cite_agent-1.0.0*
```

### Publish to Production PyPI
```bash
twine upload dist/cite_agent-1.0.0*
```

Users can then install with:
```bash
pip install cite-agent
```

---

## 🪟 Building Windows Installer (Requires Windows Machine)

On a Windows machine with Python 3.9+:

1. **Install dependencies:**
   ```powershell
   pip install pyinstaller
   ```

2. **Build binary:**
   ```powershell
   pyinstaller cite-agent.spec
   ```

3. **Create installer with Inno Setup:**
   - Install Inno Setup 6: https://jrsoftware.org/isdl.php
   - Run: `installers/windows/build.bat`
   - Output: `dist/cite-agent-setup-1.0.0.exe`

---

## 🍎 Building macOS Installer (Requires macOS)

On a macOS machine with Xcode Command Line Tools:

1. **Install dependencies:**
   ```bash
   pip install pyinstaller
   ```

2. **Build app bundle:**
   ```bash
   pyinstaller cite-agent.spec
   ```

3. **Create DMG:**
   ```bash
   cd installers/macos
   ./build_dmg.sh
   ```

4. **Optional: Code sign**
   ```bash
   codesign --sign "Developer ID Application" dist/Cite-Agent.app
   ```

   Output: `dist/cite-agent-1.0.0.dmg`

---

## 🌐 Backend Configuration

**Production Backend:** `https://cite-agent-api-720dfadd602c.herokuapp.com`

Hardcoded in: `cite_agent/account_client.py:58`

All clients automatically connect to this backend:
- Registration: `/api/auth/register`
- Login: `/api/auth/login`
- Queries: `/api/query`

---

## 📊 Distribution Checklist

### Pre-Release
- [x] Backend deployed and tested
- [x] Hardcoded backend URL in client
- [x] PyPI package built
- [x] Linux binary built
- [x] Debian package built
- [x] Binary protection (stripped, compressed)
- [x] Unnecessary files excluded
- [ ] Windows installer (requires Windows)
- [ ] macOS installer (requires macOS)
- [ ] Code signing certificates
- [ ] Update CHANGELOG.md

### Publishing
- [ ] Test PyPI upload (testpypi)
- [ ] Production PyPI upload
- [ ] GitHub Release with binaries
- [ ] Update website download links
- [ ] Announce to beta testers

### Post-Release
- [ ] Monitor backend logs
- [ ] Track installation metrics
- [ ] Collect user feedback
- [ ] Monitor API usage/quotas

---

## 🐛 Testing

### Test PyPI Package
```bash
# Create fresh environment
python3 -m venv test_env
source test_env/bin/activate

# Install package
pip install cite-agent

# Test basic functionality
cite-agent --version
cite-agent --setup  # Should prompt for email/password
```

### Test Backend Connection
```python
from cite_agent.account_client import AccountClient

client = AccountClient()
print(f"Backend URL: {client.base_url}")  # Should show Heroku URL

# Test registration (use test email)
creds = client.provision(
    email="test@university.edu",
    password="testpass123"
)
print(f"Account ID: {creds.account_id}")
print(f"JWT Token: {creds.auth_token[:20]}...")
```

### Test Binary
```bash
./dist/cite-agent --version
./dist/cite-agent --setup
```

### Test Debian Package
```bash
# Install
sudo dpkg -i dist/cite-agent_1.0.0_amd64.deb

# Run
cite-agent --version

# Uninstall
sudo apt remove cite-agent
```

---

## 📈 Next Steps

1. **Immediate (Linux only)**:
   - ✅ Publish PyPI package: `twine upload dist/cite_agent-1.0.0*`
   - ✅ Create GitHub Release with `.deb` and standalone binary
   - Announce to Linux/Python users

2. **Windows Build**:
   - Access Windows machine
   - Run `pyinstaller cite-agent.spec`
   - Build installer with Inno Setup
   - Test on clean Windows VM

3. **macOS Build**:
   - Access macOS machine
   - Run `pyinstaller cite-agent.spec`
   - Create DMG with `build_dmg.sh`
   - Code sign if Apple Developer account available

4. **Full Launch**:
   - All three platforms ready
   - Website with download links
   - Email to beta testers
   - Social media announcement

---

## 🔐 Security Notes

**What users NEVER see:**
- Groq API keys (backend has 3x keys)
- Cerebras API keys (backend has 3x keys)
- Server source code
- Database credentials
- JWT secret key

**What users DO see:**
- Their JWT access token (30-day expiry)
- Their account credentials (email/password)
- Daily usage (tokens remaining)

**Protection Layers:**
1. Backend validates all requests
2. JWT tokens expire and can be revoked
3. Daily quotas enforced server-side
4. Rate limiting prevents abuse
5. Binary distribution makes reverse engineering harder
6. API keys rotate on backend for high availability

---

## 📞 Support

For build issues:
- Check `build.log` files
- Verify Python version (3.9+)
- Ensure all dependencies installed

For distribution issues:
- Test on clean VM
- Verify file permissions
- Check binary is executable

For backend issues:
- Check Heroku logs: `heroku logs --app cite-agent-api --tail`
- Monitor `/api/health/` endpoint
- Verify environment variables set
