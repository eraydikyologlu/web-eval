"""
Executor Agent  
Test adımlarını browser-use ile yürütür.
"""

from typing import Dict, Any, Optional
import structlog
import asyncio
from pathlib import Path

logger = structlog.get_logger(__name__)


class ExecutorAgent:
    """
    Test execution'dan sorumlu agent
    - browser-use ile Playwright'i kontrol eder
    - Her step'i sırayla çalıştırır
    - Hataları yakalar ve recovery mekanizmalarını tetikler
    - Screenshot ve trace alır
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini", headless: bool = True):
        self.logger = logger.bind(agent="executor")
        self.headless = headless
        self.browser_agent = None
        self.current_page = None
        self.llm_model = llm_model
    
    def initialize_browser_tool(self, browser_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Browser session'ını başlatır
        
        Args:
            browser_config: Browser ayarları
            
        Returns:
            Initialization durumu
        """
        try:
            # Mock implementation - gerçek browser-use integration'ı burada olacak
            self.logger.info("Browser başlatılıyor", 
                           headless=self.headless,
                           browser_type=browser_config.get("browser", "chromium"))
            
            self.browser_agent = "MockBrowserAgent"
            
            return {
                "status": "success",
                "message": "Browser başarıyla başlatıldı",
                "session_id": "mock_session_123"
            }
            
        except Exception as e:
            self.logger.error("Browser başlatma hatası", error=str(e))
            return {
                "status": "error", 
                "message": f"Browser başlatılamadı: {str(e)}"
            }
    
    def execute_step_tool(self, step_data: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """
        Tek bir test step'ini çalıştırır
        
        Args:
            step_data: Step verileri 
            step_index: Step sırası
            
        Returns:
            Execution sonucu
        """
        self.logger.info("Step çalıştırılıyor", step_index=step_index, step_data=step_data)
        
        try:
            result = {"status": "success", "step_index": step_index, "duration": 0.0}
            
            # Her step türü için implementation
            if "goto" in step_data:
                result.update(self._execute_goto(step_data["goto"]))
                
            elif "fill" in step_data:
                result.update(self._execute_fill(step_data["fill"]))
                
            elif "click" in step_data:
                result.update(self._execute_click(step_data["click"]))
                
            elif "select" in step_data:
                result.update(self._execute_select(step_data["select"]))
                
            elif "assert_url_not_contains" in step_data:
                result.update(self._execute_url_assertion(step_data["assert_url_not_contains"], False))
                
            elif "assert_url_contains" in step_data:
                result.update(self._execute_url_assertion(step_data["assert_url_contains"], True))
                
            elif "wait" in step_data:
                result.update(self._execute_wait(step_data["wait"]))
                
            elif "screenshot" in step_data:
                result.update(self._execute_screenshot(step_data["screenshot"]))
                
            else:
                raise ValueError(f"Desteklenmeyen step türü: {step_data}")
            
            self.logger.info("Step başarıyla tamamlandı", step_index=step_index)
            return result
            
        except Exception as e:
            self.logger.error("Step execution hatası", 
                            step_index=step_index, 
                            error=str(e),
                            step_data=step_data)
            return {
                "status": "error",
                "step_index": step_index, 
                "error": str(e),
                "error_type": self._classify_error(str(e))
            }
    
    def take_screenshot_tool(self, filename: Optional[str] = None) -> Dict[str, str]:
        """
        Mevcut sayfa ekran görüntüsünü alır
        
        Args:
            filename: Screenshot dosya adı (optional)
            
        Returns:
            Screenshot sonucu
        """
        try:
            if not filename:
                from datetime import datetime
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            screenshot_path = Path("screenshots") / filename
            
            # Mock implementation - gerçek screenshot burada alınacak
            self.logger.info("Screenshot alınıyor", filename=filename)
            
            return {
                "status": "success",
                "path": str(screenshot_path),
                "filename": filename
            }
            
        except Exception as e:
            self.logger.error("Screenshot hatası", error=str(e))
            return {
                "status": "error",
                "message": f"Screenshot alınamadı: {str(e)}"
            }
    
    def close_browser_tool(self) -> Dict[str, str]:
        """Browser session'ını kapatır"""
        try:
            self.logger.info("Browser kapatılıyor")
            
            # Mock implementation - gerçek browser close burada olacak
            if self.browser_agent:
                # self.browser_agent.close()
                pass
            
            return {
                "status": "success",
                "message": "Browser başarıyla kapatıldı"
            }
            
        except Exception as e:
            self.logger.error("Browser kapatma hatası", error=str(e))
            return {
                "status": "error",
                "message": f"Browser kapatılamadı: {str(e)}"
            }
    
    def _execute_goto(self, url: str) -> Dict[str, Any]:
        """URL'ye git action'ını çalıştırır"""
        self.logger.info("URL'ye gidiliyor", url=url)
        
        # Mock implementation - gerçek browser navigation burada olacak
        # self.browser_agent.goto(url)
        
        return {
            "action": "goto",
            "url": url,
            "current_url": url  # Mock - gerçek current URL alınacak
        }
    
    def _execute_fill(self, fill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Form fill action'ını çalıştırır"""
        self.logger.info("Form alanı doldruluyor", fill_data=fill_data)
        
        # Mock implementation - gerçek form filling burada olacak
        
        return {
            "action": "fill",
            "field": fill_data.get("label") or fill_data.get("selector"),
            "value": fill_data["value"]
        }
    
    def _execute_click(self, click_data: Dict[str, Any]) -> Dict[str, Any]:
        """Click action'ını çalıştırır"""
        self.logger.info("Element'e tıklanıyor", click_data=click_data)
        
        # Mock implementation - gerçek clicking burada olacak
        
        return {
            "action": "click",
            "target": click_data.get("text") or click_data.get("selector")
        }
    
    def _execute_select(self, select_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select/dropdown action'ını çalıştırır"""
        self.logger.info("Dropdown seçimi yapılıyor", select_data=select_data)
        
        # Mock implementation
        return {
            "action": "select",
            "field": select_data.get("label") or select_data.get("selector"),
            "option": select_data["option"]
        }
    
    def _execute_url_assertion(self, fragment: str, should_contain: bool) -> Dict[str, Any]:
        """URL assertion'ını çalıştırır"""
        self.logger.info("URL assertion kontrol ediliyor", 
                        fragment=fragment, 
                        should_contain=should_contain)
        
        # Mock implementation - gerçek URL kontrolü burada olacak
        current_url = "http://example.com/current"  # Mock
        
        contains = fragment in current_url
        passed = contains if should_contain else not contains
        
        return {
            "action": "assert_url",
            "fragment": fragment,
            "should_contain": should_contain,
            "current_url": current_url,
            "passed": passed
        }
    
    def _execute_wait(self, wait_data: Dict[str, Any]) -> Dict[str, Any]:
        """Wait action'ını çalıştırır"""
        self.logger.info("Bekleme yapılıyor", wait_data=wait_data)
        
        if wait_data.get("seconds"):
            import time
            time.sleep(wait_data["seconds"])
        
        return {
            "action": "wait",
            "duration": wait_data.get("seconds", 0)
        }
    
    def _execute_screenshot(self, screenshot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Screenshot action'ını çalıştırır"""
        name = screenshot_data.get("name", "step_screenshot")
        full_page = screenshot_data.get("full_page", False)
        
        return self.take_screenshot_tool(f"{name}.png")
    
    def _classify_error(self, error_message: str) -> str:
        """Hata tipini sınıflandırır"""
        error_lower = error_message.lower()
        
        if "timeout" in error_lower:
            return "timeout"
        elif "not found" in error_lower or "element" in error_lower:
            return "element_not_found"
        elif "navigation" in error_lower or "load" in error_lower:
            return "navigation_failed"
        elif "network" in error_lower:
            return "network_error"
        else:
            return "unknown" 