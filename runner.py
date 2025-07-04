#!/usr/bin/env python3
"""
Modern Web Test Automation Runner
YAML senaryolarını CrewAI agent'ları ile çalıştıran ana runner.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Optional, List
import json

# Local imports
from src.utils.config import Config
from src.utils.logger import setup_logging, create_test_log_file, TestLogger
from src.utils.yaml_loader import YamlLoader
from src.agents.crew_manager import CrewManager


class TestRunner:
    """
    Ana test runner sınıfı
    CLI interface ve test execution'ı yönetir
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.crew_manager = None
        self.logger = None
        
    async def initialize(self):
        """Runner'ı başlat"""
        # Dizinleri oluştur
        self.config.ensure_directories()
        
        # Logging'i kur
        log_file = None
        if self.config.log_format == "json":
            log_file = create_test_log_file("test_runner", self.config.logs_dir)
        
        setup_logging(
            level=self.config.log_level,
            format_type=self.config.log_format,
            log_file=log_file
        )
        
        self.logger = TestLogger("test_runner")
        
        # CrewAI manager'ı başlat
        self.crew_manager = CrewManager(
            llm_model="gpt-4o-mini",
            headless=self.config.headless
        )
        
        self.logger.info("Test runner başlatıldı", config=self.config.get_all_config())
    
    async def run_single_scenario(self, scenario_path: str) -> dict:
        """
        Tek bir YAML scenario çalıştır
        
        Args:
            scenario_path: YAML dosya yolu
            
        Returns:
            Test sonuçları
        """
        self.logger.start_test()
        
        try:
            # Scenario dosyasını validate et
            validation = YamlLoader.validate_scenario_syntax(scenario_path)
            if not validation["valid"]:
                self.logger.error("Scenario validation başarısız", 
                                errors=validation["errors"])
                return {
                    "status": "validation_failed",
                    "errors": validation["errors"]
                }
            
            self.logger.info("Scenario validation başarılı", 
                           scenario_name=validation.get("scenario_name"),
                           steps_count=validation.get("steps_count"))
            
            # Test'i çalıştır
            result = await self.crew_manager.run_scenario(scenario_path)
            
            # Sonucu logla
            status = result.get("summary", {}).get("overall_status", "unknown")
            duration = result.get("metadata", {}).get("duration", 0)
            
            self.logger.end_test(status, duration)
            
            return result
            
        except Exception as e:
            self.logger.error("Test execution hatası", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def run_multiple_scenarios(self, directory: str) -> List[dict]:
        """
        Dizindeki tüm senaryoları çalıştır
        
        Args:
            directory: Test dizini
            
        Returns:
            Tüm test sonuçları
        """
        scenarios = YamlLoader.load_scenarios_from_directory(directory)
        
        if not scenarios:
            self.logger.error("Çalıştırılacak scenario bulunamadı", directory=directory)
            return []
        
        self.logger.info("Çoklu scenario execution başlıyor", 
                        scenario_count=len(scenarios))
        
        results = []
        
        for i, scenario in enumerate(scenarios):
            scenario_path = Path(directory) / f"{scenario.name}.yaml"
            
            self.logger.info("Scenario çalıştırılıyor", 
                           index=i+1, 
                           total=len(scenarios),
                           name=scenario.name)
            
            result = await self.run_single_scenario(str(scenario_path))
            results.append(result)
            
            # Kısa bir break ver
            if i < len(scenarios) - 1:
                await asyncio.sleep(1)
        
        # Özet rapor
        self._log_summary_report(results)
        
        return results
    
    def _log_summary_report(self, results: List[dict]):
        """Çoklu test sonuçları için özet rapor"""
        total_tests = len(results)
        passed = len([r for r in results if r.get("summary", {}).get("overall_status") == "passed"])
        failed = total_tests - passed
        
        self.logger.info("Test execution tamamlandı",
                        total_tests=total_tests,
                        passed=passed,
                        failed=failed,
                        success_rate=passed/total_tests if total_tests > 0 else 0)


async def main():
    """Ana CLI fonksiyonu"""
    parser = argparse.ArgumentParser(
        description="Modern Web Test Automation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # Tek bir scenario çalıştır
  python runner.py -f tests/login.yaml
  
  # Dizindeki tüm senaryoları çalıştır  
  python runner.py -d tests/
  
  # Headful modda çalıştır
  python runner.py -f tests/login.yaml --headful
  
  # Custom config ile çalıştır
  python runner.py -f tests/login.yaml --config custom.env
  
  # Örnek scenario oluştur
  python runner.py --create-example tests/example.yaml
        """
    )
    
    # Execution seçenekleri
    execution_group = parser.add_mutually_exclusive_group(required=True)
    execution_group.add_argument(
        "-f", "--file",
        help="Tek bir YAML scenario dosyası çalıştır"
    )
    execution_group.add_argument(
        "-d", "--directory", 
        help="Dizindeki tüm YAML senaryolarını çalıştır"
    )
    execution_group.add_argument(
        "--create-example",
        help="Belirtilen yolda örnek scenario oluştur"
    )
    execution_group.add_argument(
        "--validate",
        help="YAML scenario dosyasını validate et (çalıştırmadan)"
    )
    
    # Configuration seçenekleri
    parser.add_argument(
        "--config",
        help="Custom .env konfigürasyon dosyası"
    )
    parser.add_argument(
        "--headful",
        action="store_true",
        help="Browser'ı headful modda çalıştır (varsayılan: headless)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Log seviyesi"
    )
    parser.add_argument(
        "--log-format",
        choices=["json", "text"],
        default="json", 
        help="Log formatı"
    )
    
    # Output seçenekleri
    parser.add_argument(
        "--output",
        help="Test sonuçlarını JSON olarak kaydet"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Detaylı çıktı"
    )
    
    args = parser.parse_args()
    
    try:
        # Config'i yükle
        config = Config(env_file=args.config)
        
        # CLI argument'larıyla override et
        if args.headful:
            import os
            os.environ["HEADLESS"] = "false"
            
        if args.log_level:
            import os
            os.environ["LOG_LEVEL"] = args.log_level
            
        if args.log_format:
            import os
            os.environ["LOG_FORMAT"] = args.log_format
        
        # Özel komutlar
        if args.create_example:
            success = YamlLoader.create_example_scenario(args.create_example)
            if success:
                print(f"✅ Örnek scenario oluşturuldu: {args.create_example}")
                return 0
            else:
                print(f"❌ Örnek scenario oluşturulamadı: {args.create_example}")
                return 1
        
        if args.validate:
            validation = YamlLoader.validate_scenario_syntax(args.validate)
            if validation["valid"]:
                print(f"✅ Scenario syntax geçerli: {args.validate}")
                print(f"   Scenario: {validation.get('scenario_name', 'N/A')}")
                print(f"   Steps: {validation.get('steps_count', 0)}")
                return 0
            else:
                print(f"❌ Scenario syntax hatası: {args.validate}")
                for error in validation["errors"]:
                    print(f"   - {error}")
                return 1
        
        # Test runner'ı başlat
        runner = TestRunner(config)
        await runner.initialize()
        
        # Test'leri çalıştır
        results = None
        
        if args.file:
            print(f"🚀 Scenario çalıştırılıyor: {args.file}")
            results = [await runner.run_single_scenario(args.file)]
            
        elif args.directory:
            print(f"🚀 Dizindeki senaryolar çalıştırılıyor: {args.directory}")
            results = await runner.run_multiple_scenarios(args.directory)
        
        # Sonuçları kaydet
        if args.output and results:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📊 Test sonuçları kaydedildi: {args.output}")
        
        # Exit code belirle
        if results:
            failed_tests = [r for r in results if r.get("status") == "error" or 
                           r.get("summary", {}).get("overall_status") in ["failed", "partially_failed"]]
            
            if failed_tests:
                print(f"❌ {len(failed_tests)} test başarısız")
                return 1
            else:
                print(f"✅ Tüm testler başarılı")
                return 0
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution kullanıcı tarafından durduruldu")
        return 130
        
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Windows için event loop policy ayarla
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Ana fonksiyonu çalıştır
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 