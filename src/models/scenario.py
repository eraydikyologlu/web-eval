"""
Scenario ve Step modelleri
YAML test senaryolarının ana yapısını tanımlar.
"""

from typing import List, Optional, Union, Any, Dict
from pydantic import BaseModel, Field, model_validator


class Step(BaseModel):
    """
    Test adımı - YAML'deki her bir step'i temsil eder
    Sadece bir action türü aktif olabilir
    """
    # Navigation actions
    goto: Optional[str] = Field(None, description="URL'ye git")
    
    # Form actions  
    fill: Optional[Dict[str, Any]] = Field(None, description="Form alanını doldur")
    click: Optional[Dict[str, Any]] = Field(None, description="Elemente tıkla")
    select: Optional[Dict[str, Any]] = Field(None, description="Dropdown seçimi")
    
    # Assertion actions
    assert_url_not_contains: Optional[str] = Field(None, description="URL assertion")
    assert_url_contains: Optional[str] = Field(None, description="URL assertion")
    
    # Wait actions
    wait: Optional[Dict[str, Any]] = Field(None, description="Bekleme aksiyonu")
    
    # Screenshot action
    screenshot: Optional[Dict[str, Any]] = Field(None, description="Ekran görüntüsü")
    
    # Download action
    expect_download: Optional[Dict[str, Any]] = Field(None, description="Download bekleme")
    
    # Smart AI actions
    smart_fill: Optional[Dict[str, Any]] = Field(None, description="LLM ile akıllı form doldurma")
    smart_click: Optional[Dict[str, Any]] = Field(None, description="LLM ile akıllı tıklama")
    
    # Meta bilgi
    description: Optional[str] = Field(None, description="Step açıklaması")
    
    @model_validator(mode='after')
    def validate_single_action(self):
        """Sadece bir action türü aktif olabilir"""
        actions = [
            self.goto, self.fill, self.click, self.select,
            self.assert_url_not_contains, self.assert_url_contains,
            self.wait, self.screenshot, self.expect_download,
            self.smart_fill, self.smart_click
        ]
        
        active_actions = [action for action in actions if action is not None]
        
        if len(active_actions) == 0:
            raise ValueError("Her step'te en az bir action olmalı")
        
        if len(active_actions) > 1:
            raise ValueError("Her step'te sadece bir action olabilir")
        
        return self
    
    def get_action_type(self) -> str:
        """Aktif action türünü döndürür"""
        if self.goto is not None:
            return "goto"
        elif self.fill is not None:
            return "fill"
        elif self.click is not None:
            return "click"
        elif self.select is not None:
            return "select"
        elif self.assert_url_not_contains is not None:
            return "assert_url_not_contains"
        elif self.assert_url_contains is not None:
            return "assert_url_contains"
        elif self.wait is not None:
            return "wait"
        elif self.screenshot is not None:
            return "screenshot"
        elif self.expect_download is not None:
            return "expect_download"
        elif self.smart_fill is not None:
            return "smart_fill"
        elif self.smart_click is not None:
            return "smart_click"
        else:
            raise ValueError("Geçersiz action türü")
    
    def get_action_data(self) -> Any:
        """Aktif action'ın verisini döndürür"""
        action_type = self.get_action_type()
        return getattr(self, action_type)


class Scenario(BaseModel):
    """
    Test senaryosu - YAML dosyasının ana yapısı
    """
    name: Optional[str] = Field(None, description="Senaryo adı")
    description: Optional[str] = Field(None, description="Senaryo açıklaması")
    browser: Optional[str] = Field("chromium", description="Kullanılacak tarayıcı")
    headless: Optional[bool] = Field(True, description="Headless mod")
    timeout: Optional[int] = Field(30000, description="Default timeout (ms)")
    base_url: Optional[str] = Field(None, description="Base URL")
    steps: List[Step] = Field(..., description="Test adımları listesi")
    
    # Meta bilgiler
    tags: Optional[List[str]] = Field(default_factory=list, description="Senaryo etiketleri")
    retry_count: Optional[int] = Field(2, description="Hata durumunda retry sayısı")
    
    def get_step_count(self) -> int:
        """Toplam step sayısını döndürür"""
        return len(self.steps)
    
    def get_steps_by_type(self, action_type: str) -> List[Step]:
        """Belirtilen tip'teki step'leri döndürür"""
        return [step for step in self.steps if step.get_action_type() == action_type] 