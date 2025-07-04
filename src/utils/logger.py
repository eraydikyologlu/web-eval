"""
Structured Logging Setup
structlog tabanlı loglama konfigürasyonu.
"""

import structlog
import logging
import sys
from typing import Optional
from pathlib import Path
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    format_type: str = "json", 
    log_file: Optional[str] = None
) -> None:
    """
    Structured logging'i konfigüre eder
    
    Args:
        level: Log seviyesi (DEBUG, INFO, WARNING, ERROR)
        format_type: Output formatı (json, text)
        log_file: Log dosyası yolu (optional)
    """
    
    # Log seviyesini ayarla
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Timestamper ekle
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    
    # Processor'ları belirle
    shared_processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder()
    ]
    
    if format_type.lower() == "json":
        # JSON formatter
        renderer = structlog.processors.JSONRenderer()
    else:
        # Text formatter
        renderer = structlog.dev.ConsoleRenderer(
            colors=True if sys.stdout.isatty() else False
        )
    
    # structlog konfigürasyonu
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Standard logging konfigürasyonu
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=renderer,
        foreign_pre_chain=shared_processors,
    )
    
    # Handler'ları ekle
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)
    
    # File handler (opsiyonel)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Root logger'ı konfigüre et
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=handlers
    )
    
    # Test automation logger'ı ekle
    logger = structlog.get_logger("test_automation")
    logger.info("Logging configured", 
               level=level, 
               format=format_type,
               log_file=log_file)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Named logger döndürür
    
    Args:
        name: Logger adı
        
    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


def create_test_log_file(test_name: str, logs_dir: Path = Path("logs")) -> str:
    """
    Test için timestamped log dosyası oluşturur
    
    Args:
        test_name: Test adı
        logs_dir: Log dosyaları dizini
        
    Returns:
        Log dosya yolu
    """
    logs_dir.mkdir(exist_ok=True)
    
    # Timestamp ekle
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Güvenli dosya adı oluştur
    safe_test_name = "".join(c for c in test_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_test_name = safe_test_name.replace(' ', '_')
    
    log_filename = f"{safe_test_name}_{timestamp}.log"
    log_path = logs_dir / log_filename
    
    return str(log_path)


class TestLogger:
    """
    Test execution için özelleştirilmiş logger wrapper
    """
    
    def __init__(self, test_name: str, context: Optional[dict] = None):
        self.test_name = test_name
        self.context = context or {}
        self.logger = get_logger("test_execution").bind(
            test=test_name,
            **self.context
        )
    
    def start_test(self):
        """Test başlangıcını logla"""
        self.logger.info("Test starting", test_name=self.test_name)
    
    def end_test(self, status: str, duration: float):
        """Test sonunu logla"""
        self.logger.info("Test completed", 
                        test_name=self.test_name,
                        status=status,
                        duration_seconds=duration)
    
    def step_start(self, step_index: int, step_data: dict):
        """Step başlangıcını logla"""
        self.logger.info("Step starting",
                        step_index=step_index,
                        step_type=list(step_data.keys())[0] if step_data else "unknown")
    
    def step_success(self, step_index: int, duration: float):
        """Step başarısını logla"""
        self.logger.info("Step completed successfully",
                        step_index=step_index,
                        duration_seconds=duration)
    
    def step_failure(self, step_index: int, error: str, error_type: str):
        """Step hatasını logla"""
        self.logger.error("Step failed",
                         step_index=step_index,
                         error=error,
                         error_type=error_type)
    
    def recovery_attempt(self, step_index: int, attempt: int, method: str):
        """Recovery denemesini logla"""
        self.logger.warning("Recovery attempt",
                           step_index=step_index,
                           attempt=attempt,
                           method=method)
    
    def info(self, message: str, **kwargs):
        """Info seviyesinde log"""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Warning seviyesinde log"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Error seviyesinde log"""
        self.logger.error(message, **kwargs) 