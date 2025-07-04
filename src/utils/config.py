"""
Configuration Management
Environment değişkenleri ve ayarları yönetir.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """
    Test automation konfigürasyonu
    Environment değişkenleri ve default ayarları yönetir
    """
    
    def __init__(self, env_file: Optional[str] = None):
        # .env dosyasını yükle
        if env_file:
            load_dotenv(env_file)
        else:
            # Workspace root'da .env dosyasını ara
            workspace_root = Path.cwd()
            env_path = workspace_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)
    
    # OpenAI Configuration
    @property
    def openai_api_key(self) -> str:
        """OpenAI API key"""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY environment variable bulunamadı")
        return key
    
    # Browser Configuration
    @property
    def browser_type(self) -> str:
        """Kullanılacak browser türü"""
        return os.getenv("BROWSER_TYPE", "chromium")
    
    @property
    def headless(self) -> bool:
        """Headless mod aktif mi"""
        return os.getenv("HEADLESS", "true").lower() == "true"
    
    @property
    def default_timeout(self) -> int:
        """Default timeout değeri (ms)"""
        return int(os.getenv("DEFAULT_TIMEOUT", "30000"))
    
    @property
    def retry_count(self) -> int:
        """Default retry sayısı"""
        return int(os.getenv("RETRY_COUNT", "2"))
    
    # Logging Configuration
    @property
    def log_level(self) -> str:
        """Log seviyesi"""
        return os.getenv("LOG_LEVEL", "INFO")
    
    @property
    def log_format(self) -> str:
        """Log format (json/text)"""
        return os.getenv("LOG_FORMAT", "json")
    
    # Test Data
    @property
    def test_username(self) -> Optional[str]:
        """Test kullanıcı adı"""
        return os.getenv("TEST_USERNAME")
    
    @property
    def test_password(self) -> Optional[str]:
        """Test şifresi"""
        return os.getenv("TEST_PASSWORD")
    
    # Trace and Screenshot Configuration
    @property
    def trace_enabled(self) -> bool:
        """Trace kayıt aktif mi"""
        return os.getenv("TRACE_ENABLED", "true").lower() == "true"
    
    @property
    def screenshot_on_failure(self) -> bool:
        """Hata durumunda screenshot al"""
        return os.getenv("SCREENSHOT_ON_FAILURE", "true").lower() == "true"
    
    # Directories
    @property
    def tests_dir(self) -> Path:
        """Test dosyaları dizini"""
        return Path("tests")
    
    @property
    def traces_dir(self) -> Path:
        """Trace dosyaları dizini"""
        return Path("traces")
    
    @property
    def screenshots_dir(self) -> Path:
        """Screenshot dizini"""
        return Path("screenshots")
    
    @property
    def logs_dir(self) -> Path:
        """Log dosyaları dizini"""
        return Path("logs")
    
    def ensure_directories(self):
        """Gerekli dizinleri oluştur"""
        for directory in [
            self.tests_dir,
            self.traces_dir, 
            self.screenshots_dir,
            self.logs_dir
        ]:
            directory.mkdir(exist_ok=True)
    
    def get_browser_config(self) -> Dict[str, Any]:
        """Browser konfigürasyonunu dict olarak döndür"""
        return {
            "browser": self.browser_type,
            "headless": self.headless,
            "timeout": self.default_timeout,
            "trace_enabled": self.trace_enabled
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """Tüm konfigürasyonu dict olarak döndür"""
        return {
            "openai": {
                "api_key": "***" if self.openai_api_key else None
            },
            "browser": self.get_browser_config(),
            "logging": {
                "level": self.log_level,
                "format": self.log_format
            },
            "test": {
                "retry_count": self.retry_count,
                "username": self.test_username,
                "password": "***" if self.test_password else None
            },
            "directories": {
                "tests": str(self.tests_dir),
                "traces": str(self.traces_dir),
                "screenshots": str(self.screenshots_dir),
                "logs": str(self.logs_dir)
            }
        } 