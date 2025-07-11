"""
Executor Agent  
Test adımlarını Playwright ile yürütür.
"""

from typing import Dict, Any, Optional
import structlog
import asyncio
from pathlib import Path
import os
from datetime import datetime

# Playwright imports
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError

logger = structlog.get_logger(__name__)


class ExecutorAgent:
    """
    Test execution'dan sorumlu agent
    - Playwright ile browser'ı kontrol eder
    - Her step'i sırayla çalıştırır
    - Hataları yakalar ve recovery mekanizmalarını tetikler
    - Screenshot ve trace alır
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini", headless: bool = True):
        self.logger = logger.bind(agent="executor")
        self.headless = headless
        self.llm_model = llm_model
        
        # Playwright instances
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    async def initialize_browser_tool(self, browser_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Browser session'ını başlatır
        
        Args:
            browser_config: Browser ayarları
            
        Returns:
            Initialization durumu
        """
        try:
            self.logger.info("Playwright browser başlatılıyor", 
                           headless=self.headless,
                           browser_type=browser_config.get("browser", "chromium"))
            
            # Playwright'ı başlat
            self.playwright = await async_playwright().start()
            
            # Browser tipini belirle
            browser_type = browser_config.get("browser", "chromium")
            if browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(headless=self.headless)
            elif browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(headless=self.headless)
            else:  # chromium (default)
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            
            # Context oluştur
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Page oluştur
            self.page = await self.context.new_page()
            
            # Timeout ayarları
            timeout = browser_config.get("timeout", 30000)
            self.page.set_default_timeout(timeout)
            self.page.set_default_navigation_timeout(timeout)
            
            self.logger.info("Playwright browser başarıyla başlatıldı")
            
            return {
                "status": "success",
                "message": "Browser başarıyla başlatıldı",
                "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            self.logger.error("Browser başlatma hatası", error=str(e))
            await self._cleanup_browser()
            return {
                "status": "error", 
                "message": f"Browser başlatılamadı: {str(e)}"
            }
    
    async def execute_step_tool(self, step_data: Dict[str, Any], step_index: int) -> Dict[str, Any]:
        """
        Tek bir test step'ini çalıştırır
        
        Args:
            step_data: Step verileri 
            step_index: Step sırası
            
        Returns:
            Execution sonucu
        """
        self.logger.info("Step çalıştırılıyor", step_index=step_index, step_data=step_data)
        
        if not self.page:
            return {
                "status": "error",
                "step_index": step_index,
                "error": "Browser page başlatılmamış"
            }
        
        try:
            result = {"status": "success", "step_index": step_index, "duration": 0.0}
            start_time = datetime.now()
            
            # Her step türü için implementation
            if "goto" in step_data:
                result.update(await self._execute_goto(step_data["goto"]))
                
            elif "fill" in step_data:
                result.update(await self._execute_fill(step_data["fill"]))
                
            elif "click" in step_data:
                result.update(await self._execute_click(step_data["click"]))
                
            elif "select" in step_data:
                result.update(await self._execute_select(step_data["select"]))
                
            elif "assert_url_not_contains" in step_data:
                result.update(await self._execute_url_assertion(step_data["assert_url_not_contains"], False))
                
            elif "assert_url_contains" in step_data:
                result.update(await self._execute_url_assertion(step_data["assert_url_contains"], True))
                
            elif "wait" in step_data:
                result.update(await self._execute_wait(step_data["wait"]))
                
            elif "screenshot" in step_data:
                result.update(await self._execute_screenshot(step_data["screenshot"]))
                
            elif "expect_download" in step_data:
                result.update(await self._execute_expect_download(step_data["expect_download"]))
                
            else:
                raise ValueError(f"Desteklenmeyen step türü: {step_data}")
            
            result["duration"] = (datetime.now() - start_time).total_seconds()
            self.logger.info("Step başarıyla tamamlandı", step_index=step_index, duration=result["duration"])
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
    
    async def take_screenshot_tool(self, filename: Optional[str] = None) -> Dict[str, str]:
        """
        Mevcut sayfa ekran görüntüsünü alır
        
        Args:
            filename: Screenshot dosya adı (optional)
            
        Returns:
            Screenshot sonucu
        """
        try:
            if not self.page:
                return {
                    "status": "error",
                    "message": "Browser page mevcut değil"
                }
            
            if not filename:
                filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            screenshot_path = Path("screenshots") / filename
            
            # Gerçek screenshot al
            await self.page.screenshot(path=str(screenshot_path))
            
            self.logger.info("Screenshot alındı", filename=filename, path=str(screenshot_path))
            
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
    
    async def close_browser_tool(self) -> Dict[str, str]:
        """Browser session'ını kapatır"""
        try:
            self.logger.info("Browser kapatılıyor")
            await self._cleanup_browser()
            
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
    
    async def _cleanup_browser(self):
        """Browser kaynaklarını temizle"""
        try:
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            self.page = None
            
        except Exception as e:
            self.logger.warning("Browser cleanup hatası", error=str(e))
    
    async def _execute_goto(self, url: str) -> Dict[str, Any]:
        """URL'ye git action'ını çalıştırır"""
        self.logger.info("URL'ye gidiliyor", url=url)
        
        try:
            await self.page.goto(url, wait_until="load")
            current_url = self.page.url
            
            return {
                "action": "goto",
                "url": url,
                "current_url": current_url
            }
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Sayfa yüklenirken timeout: {url}")
    
    async def _execute_fill(self, fill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Form fill action'ını çalıştırır"""
        self.logger.info("Form alanı doldruluyor", fill_data=fill_data)
        
        value = fill_data["value"]
        
        # Selector'ı belirle
        if "label" in fill_data:
            # Label ile element bulma
            selector = f"input[aria-label='{fill_data['label']}'], label:has-text('{fill_data['label']}') + input, label:has-text('{fill_data['label']}') input"
        elif "placeholder" in fill_data:
            # Placeholder ile element bulma
            selector = f"input[placeholder='{fill_data['placeholder']}']"
        elif "selector" in fill_data:
            # Direkt selector
            selector = fill_data["selector"]
        else:
            raise ValueError("Fill action için label, placeholder veya selector gerekli")
        
        try:
            # Element'i bekle ve doldur
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.fill(selector, value)
            
            # Dijidemi arama kutusu için özel tetikleme
            if selector == "#search_tb":
                self.logger.info("Dijidemi arama kutusu için JavaScript eventi tetikleniyor")
                # Space ekle ve backspace bas (arama fonksiyonunu tetiklemek için)
                await self.page.press(selector, " ")
                await self.page.press(selector, "Backspace")
            
            return {
                "action": "fill",
                "field": fill_data.get("label") or fill_data.get("placeholder") or fill_data.get("selector"),
                "value": value
            }
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Form alanı bulunamadı: {selector}")
    
    async def _execute_click(self, click_data: Dict[str, Any]) -> Dict[str, Any]:
        """Click action'ını çalıştırır"""
        self.logger.info("Element'e tıklanıyor", click_data=click_data)
        
        # Selector'ı belirle
        if "text" in click_data:
            # Text ile element bulma
            selector = f"text={click_data['text']}"
        elif "selector" in click_data:
            # Direkt selector
            selector = click_data["selector"]
        elif "label" in click_data:
            # Aria-label ile element bulma
            selector = f"[aria-label='{click_data['label']}']"
        else:
            raise ValueError("Click action için text, selector veya label gerekli")
        
        try:
            # Element'i bekle ve tıkla
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.click(selector)
            
            return {
                "action": "click",
                "target": click_data.get("text") or click_data.get("selector") or click_data.get("label")
            }
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Tıklanacak element bulunamadı: {selector}")
    
    async def _execute_select(self, select_data: Dict[str, Any]) -> Dict[str, Any]:
        """Select/dropdown action'ını çalıştırır"""
        self.logger.info("Dropdown seçimi yapılıyor", select_data=select_data)
        
        option = select_data["option"]
        
        # Selector'ı belirle
        if "label" in select_data:
            # Label ile select bulma
            selector = f"select[aria-label='{select_data['label']}'], label:has-text('{select_data['label']}') + select, label:has-text('{select_data['label']}') select"
        elif "selector" in select_data:
            # Direkt selector
            selector = select_data["selector"]
        else:
            raise ValueError("Select action için label veya selector gerekli")
        
        try:
            # Element'i bekle ve seç
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.select_option(selector, label=option)
            
            return {
                "action": "select",
                "field": select_data.get("label") or select_data.get("selector"),
                "option": option
            }
        except PlaywrightTimeoutError:
            raise TimeoutError(f"Dropdown bulunamadı: {selector}")
    
    async def _execute_url_assertion(self, fragment: str, should_contain: bool) -> Dict[str, Any]:
        """URL assertion'ını çalıştırır"""
        self.logger.info("URL assertion kontrol ediliyor", 
                        fragment=fragment, 
                        should_contain=should_contain)
        
        # Current URL'yi al
        current_url = self.page.url
        
        contains = fragment in current_url
        passed = contains if should_contain else not contains
        
        if not passed:
            action_type = "contains" if should_contain else "not_contains"
            raise AssertionError(f"URL assertion failed: expected URL to {action_type} '{fragment}', but current URL is '{current_url}'")
        
        return {
            "action": "assert_url",
            "fragment": fragment,
            "should_contain": should_contain,
            "current_url": current_url,
            "passed": passed
        }
    
    async def _execute_wait(self, wait_data: Dict[str, Any]) -> Dict[str, Any]:
        """Wait action'ını çalıştırır"""
        self.logger.info("Bekleme yapılıyor", wait_data=wait_data)
        
        if wait_data.get("seconds"):
            await asyncio.sleep(wait_data["seconds"])
            return {
                "action": "wait",
                "duration": wait_data["seconds"]
            }
        elif wait_data.get("for_element"):
            # Element'in görünmesini bekle
            selector = wait_data["for_element"]
            try:
                await self.page.wait_for_selector(selector, timeout=30000)
                return {
                    "action": "wait",
                    "for_element": selector
                }
            except PlaywrightTimeoutError:
                raise TimeoutError(f"Element görünmedi: {selector}")
        elif wait_data.get("for_url_contains"):
            # URL değişikliği için bekle
            fragment = wait_data["for_url_contains"]
            try:
                await self.page.wait_for_url(f"**/*{fragment}*", timeout=30000)
                return {
                    "action": "wait",
                    "for_url_contains": fragment
                }
            except PlaywrightTimeoutError:
                raise TimeoutError(f"URL değişmedi: {fragment}")
        else:
            return {
                "action": "wait",
                "duration": 0
            }
    
    async def _execute_screenshot(self, screenshot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Screenshot action'ını çalıştırır"""
        name = screenshot_data.get("name", "step_screenshot")
        full_page = screenshot_data.get("full_page", False)
        
        filename = f"{name}.png"
        
        if not self.page:
            return {
                "status": "error",
                "message": "Browser page mevcut değil"
            }
        
        screenshot_path = Path("screenshots") / filename
        
        try:
            # Full page screenshot
            await self.page.screenshot(
                path=str(screenshot_path),
                full_page=full_page
            )
            
            self.logger.info("Screenshot alındı", filename=filename, full_page=full_page)
            
            return {
                "action": "screenshot",
                "name": name,
                "path": str(screenshot_path),
                "full_page": full_page
            }
        except Exception as e:
            raise RuntimeError(f"Screenshot alınamadı: {str(e)}")
    
    async def evaluate_javascript_tool(self, script: str) -> Dict[str, Any]:
        """
        JavaScript kodunu çalıştırır ve sonucu döndürür
        
        Args:
            script: Çalıştırılacak JavaScript kodu
            
        Returns:
            JavaScript execution sonucu
        """
        try:
            if not self.page:
                return {
                    "status": "error",
                    "message": "Browser page mevcut değil"
                }
            
            # JavaScript'i çalıştır
            result = await self.page.evaluate(script)
            
            self.logger.info("JavaScript çalıştırıldı", script_length=len(script))
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            self.logger.error("JavaScript hatası", error=str(e), script=script[:100])
            return {
                "status": "error",
                "message": f"JavaScript çalıştırılamadı: {str(e)}"
            }
    
    async def _execute_expect_download(self, download_data: Dict[str, Any]) -> Dict[str, Any]:
        """Download bekleme action'ını çalıştırır"""
        self.logger.info("Download bekleniyor", download_data=download_data)
        
        try:
            # Download event'ini bekle
            async with self.page.expect_download(timeout=30000) as download_info:
                # Download'ı tetikleyecek elementi tıkla
                if "trigger_selector" in download_data:
                    await self.page.click(download_data["trigger_selector"])
                elif "trigger_text" in download_data:
                    await self.page.click(f"text={download_data['trigger_text']}")
            
            download = await download_info.value
            
            # Download bilgilerini al
            filename = download.suggested_filename
            
            self.logger.info("Download başarıyla başlatıldı", 
                           filename=filename)
            
            return {
                "action": "expect_download",
                "filename": filename,
                "status": "download_started"
            }
            
        except Exception as e:
            self.logger.error("Download bekleme hatası", error=str(e))
            raise TimeoutError(f"Download başlatılamadı: {str(e)}")

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
        elif "assertion" in error_lower:
            return "assertion_failed"
        else:
            return "unknown" 