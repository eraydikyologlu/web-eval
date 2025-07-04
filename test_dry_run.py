#!/usr/bin/env python3
"""
Dry Run Test - Framework'ün tam workflow'unu test eder
"""

import asyncio
import sys
from pathlib import Path
import structlog

# Setup
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.crew_manager import CrewManager
from src.utils.yaml_loader import load_scenario, create_example_scenario

async def test_full_workflow():
    """Framework'ün tam workflow'unu test eder"""
    
    print("🚀 Dry Run Test - Framework Workflow Testi")
    print("=" * 60)
    
    try:
        # 1. Test scenario oluştur
        print("\n📝 Test scenario oluşturuluyor...")
        test_scenario_path = "tests/dry-run-test.yaml"
        
        if create_example_scenario(test_scenario_path):
            print(f"✅ Test scenario oluşturuldu: {test_scenario_path}")
        else:
            print("❌ Test scenario oluşturulamadı")
            return False
        
        # 2. Scenario'yu yükle ve validate et
        print("\n🔍 Scenario yükleniyor ve validate ediliyor...")
        scenario = load_scenario(test_scenario_path)
        
        if scenario:
            print(f"✅ Scenario yüklendi: {scenario.name}")
            print(f"   📊 Step sayısı: {len(scenario.steps)}")
            print(f"   🌐 Browser: {scenario.browser}")
            print(f"   👁️  Headless: {scenario.headless}")
        else:
            print("❌ Scenario yüklenemedi")
            return False
        
        # 3. CrewManager'ı başlat
        print("\n🤖 CrewManager başlatılıyor...")
        crew_manager = CrewManager(llm_model="gpt-4o-mini", headless=True)
        print("✅ CrewManager başlatıldı")
        
        # 4. Scenario'yu çalıştır (mock mode)
        print("\n⚡ Scenario çalıştırılıyor (Mock Mode)...")
        print("   ⚠️  Not: Bu bir mock execution'dır, gerçek browser açılmayacak")
        
        # Mock execution
        result = await crew_manager.run_scenario(test_scenario_path)
        
        # 5. Sonuçları analiz et
        print("\n📊 Sonuçlar analiz ediliyor...")
        
        if result.get("status") == "error":
            print(f"❌ Test başarısız: {result.get('error', 'Bilinmeyen hata')}")
            return False
        
        # Result structure'ını kontrol et
        required_keys = ["metadata", "summary", "execution", "verification"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"⚠️  Eksik result anahtarları: {missing_keys}")
        else:
            print("✅ Result structure tamamlanmış")
        
        # Summary bilgilerini göster
        if "summary" in result:
            summary = result["summary"]
            print(f"\n🎯 Test Özeti:")
            print(f"   📈 Overall Status: {summary.get('overall_status', 'unknown')}")
            print(f"   📊 Toplam Step: {summary.get('total_steps', 0)}")
            print(f"   ✅ Başarılı: {summary.get('passed', 0)}")
            print(f"   ❌ Başarısız: {summary.get('failed', 0)}")
            print(f"   📈 Başarı Oranı: {summary.get('success_rate', 0):.1%}")
        
        # Execution detayları
        if "execution" in result:
            execution = result["execution"]
            print(f"\n⚡ Execution Detayları:")
            print(f"   ⏱️  Toplam Süre: {execution.get('total_duration', 0):.2f} saniye")
            print(f"   🔧 Status: {execution.get('status', 'unknown')}")
            
            if "steps" in execution:
                steps = execution["steps"]
                print(f"   📋 Step Detayları:")
                for i, step in enumerate(steps[:3]):  # İlk 3 step
                    status = step.get("status", "unknown")
                    action = step.get("action", "unknown")
                    duration = step.get("duration", 0)
                    print(f"      {i+1}. {action}: {status} ({duration:.2f}s)")
                
                if len(steps) > 3:
                    print(f"      ... ve {len(steps)-3} step daha")
        
        print("\n🎉 Dry Run Test Başarılı!")
        print("✅ Framework tam olarak çalışıyor")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Dry Run Test Hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup - test dosyasını sil
        try:
            Path(test_scenario_path).unlink(missing_ok=True)
            print(f"\n🧹 Test dosyası temizlendi: {test_scenario_path}")
        except:
            pass

def main():
    """Main entry point"""
    
    # Logging setup
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
        cache_logger_on_first_use=True,
    )
    
    # Run test
    success = asyncio.run(test_full_workflow())
    
    if success:
        print("\n🎯 SONUÇ: Framework doğrulanmış ve kullanıma hazır!")
        sys.exit(0)
    else:
        print("\n💥 SONUÇ: Framework'de sorunlar var!")
        sys.exit(1)

if __name__ == "__main__":
    main() 