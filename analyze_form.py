#!/usr/bin/env python3
"""
Dijidemi form elemanlarını analiz eder
"""

import asyncio
from src.agents.executor import ExecutorAgent


async def analyze_form():
    """Dijidemi login form elemanlarını analiz eder"""
    
    print("🔍 Dijidemi Form Analizi Başlıyor...")
    
    # ExecutorAgent'ı başlat
    executor = ExecutorAgent(headless=False)
    
    # Browser'ı başlat
    browser_config = {
        "browser": "chromium",
        "headless": False,
        "timeout": 30000
    }
    
    init_result = await executor.initialize_browser_tool(browser_config)
    if init_result["status"] != "success":
        print(f"❌ Browser başlatılamadı: {init_result['message']}")
        return
    
    try:
        # Dijidemi login sayfasına git
        print("🌐 Dijidemi.com/Login sayfasına gidiliyor...")
        goto_result = await executor._execute_goto("https://dijidemi.com/Login")
        print(f"✅ Sayfa yüklendi: {goto_result['current_url']}")
        
        # 3 saniye bekle
        await asyncio.sleep(3)
        
        # Form elemanlarını analiz et
        print("🔍 Form elemanları analiz ediliyor...")
        
        js_script = """
        () => {
            const inputs = Array.from(document.querySelectorAll('input'));
            const buttons = Array.from(document.querySelectorAll('button'));
            const selects = Array.from(document.querySelectorAll('select'));
            
            const formElements = [];
            
            inputs.forEach((input, index) => {
                formElements.push({
                    type: 'input',
                    index: index,
                    id: input.id || 'no-id',
                    name: input.name || 'no-name',
                    placeholder: input.placeholder || 'no-placeholder',
                    value: input.value || 'no-value',
                    type_attr: input.type || 'no-type',
                    className: input.className || 'no-class',
                    ariaLabel: input.getAttribute('aria-label') || 'no-aria-label',
                    outerHTML: input.outerHTML.substring(0, 200)
                });
            });
            
            buttons.forEach((button, index) => {
                formElements.push({
                    type: 'button',
                    index: index,
                    id: button.id || 'no-id',
                    text: button.textContent.trim() || 'no-text',
                    className: button.className || 'no-class',
                    ariaLabel: button.getAttribute('aria-label') || 'no-aria-label',
                    outerHTML: button.outerHTML.substring(0, 200)
                });
            });
            
            selects.forEach((select, index) => {
                formElements.push({
                    type: 'select',
                    index: index,
                    id: select.id || 'no-id',
                    name: select.name || 'no-name',
                    className: select.className || 'no-class',
                    ariaLabel: select.getAttribute('aria-label') || 'no-aria-label',
                    outerHTML: select.outerHTML.substring(0, 200)
                });
            });
            
            return formElements;
        }
        """
        
        js_result = await executor.evaluate_javascript_tool(js_script)
        
        if js_result["status"] == "success":
            elements = js_result["result"]
            print(f"\n📋 Bulunan {len(elements)} form elemanı:")
            print("=" * 80)
            
            for element in elements:
                print(f"\n🔹 {element['type'].upper()} #{element['index']}")
                print(f"   ID: {element['id']}")
                if 'name' in element:
                    print(f"   Name: {element['name']}")
                if 'placeholder' in element:
                    print(f"   Placeholder: {element['placeholder']}")
                if 'text' in element:
                    print(f"   Text: {element['text']}")
                if 'type_attr' in element:
                    print(f"   Type: {element['type_attr']}")
                print(f"   Class: {element['className']}")
                print(f"   Aria-Label: {element['ariaLabel']}")
                print(f"   HTML: {element['outerHTML'][:100]}...")
                
        else:
            print(f"❌ JavaScript hatası: {js_result['message']}")
            
        # Screenshot al
        print("\n📸 Screenshot alınıyor...")
        screenshot_result = await executor.take_screenshot_tool("form_analysis.png")
        if screenshot_result["status"] == "success":
            print(f"✅ Screenshot kaydedildi: {screenshot_result['path']}")
        
    finally:
        # Browser'ı kapat
        await executor.close_browser_tool()
        print("🏁 Analiz tamamlandı!")


if __name__ == "__main__":
    asyncio.run(analyze_form()) 