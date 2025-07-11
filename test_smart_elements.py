#!/usr/bin/env python3
"""
Smart Element Selection Demo
LLM ile akıllı element seçimi test eder
"""

import asyncio
from src.agents.executor import ExecutorAgent


async def test_smart_elements():
    """Smart element selection test'i"""
    
    print("🧠 LLM ile Akıllı Element Seçimi Test Başlıyor...")
    
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
        
        # 2 saniye bekle
        await asyncio.sleep(2)
        
        print("\n📋 Sayfa elementleri analiz ediliyor...")
        elements_result = await executor.analyze_page_elements_tool()
        
        if elements_result["status"] == "success":
            elements = elements_result["elements"]
            print(f"✅ {len(elements)} element bulundu!")
            
            # İlk 5 elementi göster
            print("\n🔍 İlk 5 Element:")
            for i, el in enumerate(elements[:5]):
                print(f"   {i}: {el['tagName']} id='{el['id']}' text='{el['text'][:30]}...'")
        
        print("\n🧠 LLM ile kullanıcı adı alanını seçmeye çalışıyor...")
        smart_fill_result = await executor.smart_fill_tool("kullanıcı adını gir", "test_user")
        
        if smart_fill_result["status"] == "success":
            print(f"✅ Smart fill başarılı! Element: {smart_fill_result['element']['id']}")
        else:
            print(f"❌ Smart fill hatası: {smart_fill_result['message']}")
        
        print("\n🧠 LLM ile şifre alanını seçmeye çalışıyor...")
        smart_fill_result2 = await executor.smart_fill_tool("şifre gir", "test123")
        
        if smart_fill_result2["status"] == "success":
            print(f"✅ Smart fill başarılı! Element: {smart_fill_result2['element']['id']}")
        else:
            print(f"❌ Smart fill hatası: {smart_fill_result2['message']}")
        
        print("\n🧠 LLM ile giriş butonunu seçmeye çalışıyor...")
        smart_click_result = await executor.smart_click_tool("giriş butonuna tıkla")
        
        if smart_click_result["status"] == "success":
            print(f"✅ Smart click başarılı! Element: {smart_click_result['element']['id']}")
        else:
            print(f"❌ Smart click hatası: {smart_click_result['message']}")
            
        # 3 saniye bekle
        await asyncio.sleep(3)
            
    finally:
        # Browser'ı kapat
        await executor.close_browser_tool()
        print("🏁 Test tamamlandı!")


if __name__ == "__main__":
    asyncio.run(test_smart_elements()) 