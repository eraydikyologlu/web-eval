# 🤖 Modern Web Test Automation

**LLM-Yerleşik**, **Agent-Tabanlı** ve **YAML-Driven** modern web test otomasyon framework'ü.

## 🚀 Özellikler

### ✨ Ana Özellikler
- **🧠 LLM-Entegre**: OpenAI GPT-4o-mini ile akıllı element bulma
- **🤝 Multi-Agent**: CrewAI ile Planner/Executor/Verifier agents
- **📝 YAML DSL**: Kodlama gerektirmeyen test senaryoları
- **🎭 Playwright**: Modern browser automation
- **📊 Zengin Raporlama**: Structured logging ve detaylı analiz
- **🔄 Auto-Recovery**: Akıllı hata düzeltme mekanizmaları

### 🛠 Teknoloji Stack'i
- **Browser**: Playwright (Chromium/Firefox/Safari)
- **AI Layer**: browser-use + OpenAI GPT-4o-mini
- **Orchestration**: CrewAI multi-agent framework
- **DSL**: YAML + Pydantic validation
- **Logging**: structlog JSON logging
- **Language**: Python 3.12+

## 📦 Kurulum

### 1. Environment Hazırlığı

```bash
# Python 3.12+ gerekli
python --version

# Virtual environment oluştur
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac  
source .venv/bin/activate
```

### 2. Dependencies

```bash
# Paketleri yükle
pip install -r requirements.txt

# Playwright browsers
playwright install chromium firefox webkit
```

### 3. Configuration

```bash
# Environment dosyasını oluştur
cp env.example .env

# .env dosyasını düzenle
# OPENAI_API_KEY=your_api_key_here
```

## 🎯 Hızlı Başlangıç

### 1. Örnek Scenario Oluştur

```bash
python runner.py --create-example tests/my-test.yaml
```

### 2. Scenario'yu Validate Et

```bash
python runner.py --validate tests/my-test.yaml
```

### 3. Test'i Çalıştır

```bash
# Tek scenario
python runner.py -f tests/my-test.yaml

# Tüm testler
python runner.py -d tests/

# Headful modda (debug için)
python runner.py -f tests/my-test.yaml --headful
```

## 📝 YAML DSL Rehberi

### Temel Yapı

```yaml
name: "Test Adı"
description: "Test açıklaması"
browser: chromium          # chromium, firefox, webkit
headless: true             # true/false
timeout: 30000            # milliseconds
retry_count: 2

steps:
  - goto: "https://example.com"
  - fill: { label: "Username", value: "user123" }
  - click: { text: "Login" }
  - assert_url_contains: "dashboard"
```

### Desteklenen Actions

#### 🌐 Navigation
```yaml
- goto: "https://example.com"
```

#### ✏️ Form Actions
```yaml
# Label ile
- fill: { label: "Email", value: "test@example.com" }

# Placeholder ile  
- fill: { placeholder: "Enter email", value: "test@example.com" }

# CSS Selector ile
- fill: { selector: "#email", value: "test@example.com" }
```

#### 🖱️ Click Actions
```yaml
# Text ile
- click: { text: "Login" }

# CSS Selector ile
- click: { selector: "#login-btn" }

# Aria-label ile
- click: { label: "Submit Form" }
```

#### 📋 Select Actions
```yaml
- select: { label: "Country", option: "Turkey" }
- select: { selector: "#country", option: "TR" }
```

#### ✅ Assertions
```yaml
- assert_url_contains: "dashboard"
- assert_url_not_contains: "login"
```

#### ⏱️ Wait Actions
```yaml
# Süre bazlı
- wait: { seconds: 2 }

# Element bazlı
- wait: { for_element: "#loading" }

# URL bazlı
- wait: { for_url_contains: "loaded" }
```

#### 📸 Screenshot
```yaml
- screenshot: { name: "step1", full_page: false }
- screenshot: { name: "full_page", full_page: true }
```

## 🏗️ Mimari

### Multi-Agent Yapı

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   🎯 Planner    │───▶│  ⚡ Executor    │───▶│  ✅ Verifier   │
│                 │    │                 │    │                 │
│ • Risk analizi  │    │ • Step exec     │    │ • Sonuç analiz  │
│ • Plan oluştur  │    │ • Error handle  │    │ • Rapor oluştur │
│ • Recovery      │    │ • Recovery      │    │ • Kalite skoru  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 📁 Proje Yapısı

```
web-eval/
├── src/
│   ├── agents/          # CrewAI agents
│   │   ├── planner.py   # Test planning agent
│   │   ├── executor.py  # Test execution agent  
│   │   ├── verifier.py  # Result verification agent
│   │   └── crew_manager.py # Agent orchestration
│   ├── models/          # Pydantic models
│   │   ├── scenario.py  # YAML DSL models
│   │   └── actions.py   # Action type definitions
│   └── utils/           # Utilities
│       ├── config.py    # Configuration management
│       ├── logger.py    # Structured logging
│       └── yaml_loader.py # YAML scenario loader
├── tests/               # YAML test scenarios
├── traces/              # Playwright traces
├── screenshots/         # Test screenshots  
├── logs/                # Structured logs
├── runner.py            # Main CLI runner
└── requirements.txt     # Dependencies
```

## 🔧 CLI Kullanımı

### Test Execution

```bash
# Tek dosya
python runner.py -f tests/login.yaml

# Dizin
python runner.py -d tests/

# Headful mod (debug)
python runner.py -f tests/login.yaml --headful

# Custom config
python runner.py -f tests/login.yaml --config my.env

# Sonuçları kaydet
python runner.py -f tests/login.yaml --output results.json
```

### Utilities

```bash
# Örnek oluştur
python runner.py --create-example tests/new-test.yaml

# Validate et
python runner.py --validate tests/my-test.yaml

# Verbose output
python runner.py -f tests/login.yaml --verbose

# Log format
python runner.py -f tests/login.yaml --log-format text
```

## 📊 Logging & Observability

### Structured Logging

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info", 
  "agent": "executor",
  "step_index": 2,
  "action": "click",
  "target": "Login Button",
  "duration_ms": 1250,
  "status": "success"
}
```

### Artifacts

- **Screenshots**: `screenshots/` - Hata ve checkpoint'lerde
- **Traces**: `traces/` - Playwright execution traces  
- **Logs**: `logs/` - Structured JSON logs
- **Reports**: Test sonuç raporları

## 🔍 Hata Ayıklama

### Headful Mode

```bash
python runner.py -f tests/login.yaml --headful --log-format text
```

### Playwright Traces

```bash
# Trace dosyasını görüntüle
playwright show-trace traces/test_trace.zip
```

### Verbose Logging

```bash
python runner.py -f tests/login.yaml --log-level DEBUG --verbose
```

## 🚦 CI/CD Entegrasyonu

### GitHub Actions

```yaml
name: Web Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - run: pip install -r requirements.txt
      - run: playwright install --with-deps
      
      - name: Run Tests  
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: python runner.py -d tests/ --output results.json
      
      - uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: |
            results.json
            traces/
            screenshots/
```

## 🛡️ Güvenlik

### Environment Variables

```bash
# .env dosyası
OPENAI_API_KEY=sk-...
TEST_USERNAME=your_test_user  
TEST_PASSWORD=your_test_pass

# Secrets Manager (Production)
# AWS Secrets Manager, Azure Key Vault, etc.
```

### API Key Güvenliği

- ✅ `.env` dosyaları `.gitignore`'da
- ✅ Production'da environment variables
- ✅ Least privilege API keys
- ✅ Log'larda API key masking

## 📈 Performance

### Optimizasyon Tips

1. **Parallel Execution**: Bağımsız test'leri paralel çalıştır
2. **Smart Waiting**: Fixed wait yerine dynamic wait kullan
3. **Selective Screenshots**: Sadece gerektiğinde screenshot al
4. **Trace Control**: Heavy trace'leri sadece failure'da aktif et

### Metrics

- **Step Duration**: Her step'in süre analizi
- **Success Rate**: Test reliability metrikleri  
- **Recovery Rate**: Auto-healing başarı oranı
- **Quality Score**: Test kalite skoru

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit yapın (`git commit -m 'Add amazing feature'`)
4. Push yapın (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 🆘 Destek

- **Issues**: GitHub Issues üzerinden sorun bildirin
- **Discussions**: Genel sorular için GitHub Discussions  
- **Wiki**: Detaylı dokümantasyon için Wiki

---

**⚡ Geliştirildi:** Modern AI-powered test automation ile manuel test yazma dönemini bitirdik! 