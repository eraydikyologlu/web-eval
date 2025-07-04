#!/usr/bin/env python3
"""
Temel fonksiyonaliteyi test et
CrewAI ve browser-use olmadan temel bileşenleri kontrol eder.
"""

import sys
from pathlib import Path

def test_yaml_creation():
    """YAML scenario oluşturma testi"""
    print("🧪 YAML scenario oluşturma testi...")
    
    try:
        from src.utils.yaml_loader import YamlLoader
        
        # Test scenario oluştur
        output_path = "tests/test_example.yaml"
        success = YamlLoader.create_example_scenario(output_path)
        
        if success and Path(output_path).exists():
            print("✅ YAML scenario başarıyla oluşturuldu")
            
            # Oluşturulan dosyayı oku
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"📄 Dosya içeriği ({len(content)} karakter)")
                
            # Dosyayı temizle
            Path(output_path).unlink()
            return True
        else:
            print("❌ YAML scenario oluşturulamadı")
            return False
            
    except Exception as e:
        print(f"❌ YAML test hatası: {str(e)}")
        return False

def test_config():
    """Config testi"""
    print("\n🧪 Config testi...")
    
    try:
        from src.utils.config import Config
        
        config = Config()
        
        # Basic properties
        browser = config.browser_type
        headless = config.headless
        timeout = config.default_timeout
        
        print(f"✅ Config yüklendi - Browser: {browser}, Headless: {headless}, Timeout: {timeout}")
        return True
        
    except Exception as e:
        print(f"❌ Config test hatası: {str(e)}")
        return False

def test_models():
    """Pydantic modelleri testi"""
    print("\n🧪 Pydantic modelleri testi...")
    
    try:
        from src.models.scenario import Scenario, Step
        
        # Test step oluştur
        test_step = Step(goto="https://example.com")
        print(f"✅ Step modeli: {test_step.get_action_type()}")
        
        # Test scenario oluştur
        test_scenario = Scenario(
            name="Test Scenario",
            steps=[test_step]
        )
        print(f"✅ Scenario modeli: {test_scenario.name} ({test_scenario.get_step_count()} steps)")
        return True
        
    except Exception as e:
        print(f"❌ Models test hatası: {str(e)}")
        return False

def test_logging():
    """Logging testi"""
    print("\n🧪 Logging testi...")
    
    try:
        from src.utils.logger import setup_logging, get_logger
        
        # Logging'i kur
        setup_logging(level="INFO", format_type="text")
        
        # Logger al ve test et
        logger = get_logger("test")
        logger.info("Test log mesajı")
        
        print("✅ Logging sistemi çalışıyor")
        return True
        
    except Exception as e:
        print(f"❌ Logging test hatası: {str(e)}")
        return False

def test_directory_structure():
    """Dizin yapısını kontrol et"""
    print("\n🧪 Dizin yapısı testi...")
    
    expected_dirs = [
        "src", "src/agents", "src/models", "src/utils",
        "tests", "traces", "screenshots", "logs"
    ]
    
    missing_dirs = []
    for dir_path in expected_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"❌ Eksik dizinler: {missing_dirs}")
        return False
    else:
        print("✅ Tüm dizinler mevcut")
        return True

def main():
    """Ana test fonksiyonu"""
    print("🚀 Modern Web Test Automation - Temel Bileşen Testleri\n")
    
    tests = [
        ("Dizin Yapısı", test_directory_structure),
        ("Config", test_config),
        ("Pydantic Modelleri", test_models),
        ("Logging", test_logging),
        ("YAML Oluşturma", test_yaml_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test exception: {str(e)}")
    
    print(f"\n📊 Test Sonuçları: {passed}/{total} başarılı")
    
    if passed == total:
        print("🎉 Tüm temel testler başarılı! Framework hazır.")
        return 0
    else:
        print("⚠️  Bazı testler başarısız. Lütfen hataları düzeltin.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 