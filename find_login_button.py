#!/usr/bin/env python3
"""
Dijidemi Giriş Yap butonunu bulur
"""

import asyncio
from src.agents.executor import ExecutorAgent


async def find_login_button():
    """Giriş Yap butonunu bulur"""
    
    print("🔍 Giriş Yap Butonu Aranıyor...")
    
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
        await executor._execute_goto("https://dijidemi.com/Login")
        
        # 3 saniye bekle
        await asyncio.sleep(3)
        
        # Tüm butonları, linkleri ve form elemanlarını ara
        js_script = """
        () => {
            const elements = [];
            
            // Tüm button, input[type=submit], input[type=button], a elemanlarını ara
            const allElements = document.querySelectorAll('button, input[type=submit], input[type=button], a, [onclick], .btn');
            
            allElements.forEach((el, index) => {
                const text = el.textContent.trim();
                const onClick = el.getAttribute('onclick') || '';
                const className = el.className || '';
                const id = el.id || '';
                
                // "Giriş", "Login", "Oturum" gibi kelimeler ara
                if (text.toLowerCase().includes('giriş') || 
                    text.toLowerCase().includes('login') || 
                    text.toLowerCase().includes('oturum') ||
                    onClick.toLowerCase().includes('login') ||
                    className.toLowerCase().includes('login') ||
                    id.toLowerCase().includes('login') ||
                    text.includes('Gir')) {
                    
                    elements.push({
                        index: index,
                        tagName: el.tagName.toLowerCase(),
                        id: id,
                        className: className,
                        text: text,
                        onclick: onClick,
                        type: el.type || 'no-type',
                        href: el.href || 'no-href',
                        outerHTML: el.outerHTML.substring(0, 300)
                    });
                }
            });
            
            return elements;
        }
        """
        
        js_result = await executor.evaluate_javascript_tool(js_script)
        
        if js_result["status"] == "success":
            elements = js_result["result"]
            print(f"\n📋 Bulunan {len(elements)} giriş ile ilgili element:")
            print("=" * 80)
            
            for element in elements:
                print(f"\n🔹 {element['tagName'].upper()} #{element['index']}")
                print(f"   ID: {element['id']}")
                print(f"   Class: {element['className']}")
                print(f"   Text: '{element['text']}'")
                print(f"   OnClick: {element['onclick']}")
                print(f"   Type: {element['type']}")
                print(f"   Href: {element['href']}")
                print(f"   HTML: {element['outerHTML'][:150]}...")
                
        else:
            print(f"❌ JavaScript hatası: {js_result['message']}")
            
    finally:
        # Browser'ı kapat
        await executor.close_browser_tool()
        print("🏁 Analiz tamamlandı!")


if __name__ == "__main__":
    asyncio.run(find_login_button()) 