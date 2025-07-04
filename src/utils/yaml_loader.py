"""
YAML Scenario Loader
Test senaryolarını yükler ve validate eder.
"""

import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from pydantic import ValidationError
import structlog

from ..models.scenario import Scenario

logger = structlog.get_logger(__name__)


class YamlLoader:
    """
    YAML test senaryolarını yükler ve validate eder
    """
    
    @staticmethod
    def load_scenario(file_path: str) -> Optional[Scenario]:
        """
        YAML dosyasından test senaryosunu yükler
        
        Args:
            file_path: YAML dosya yolu
            
        Returns:
            Validate edilmiş Scenario objesi veya None
        """
        try:
            scenario_path = Path(file_path)
            
            if not scenario_path.exists():
                logger.error("Scenario dosyası bulunamadı", path=file_path)
                return None
            
            if not scenario_path.suffix.lower() in ['.yaml', '.yml']:
                logger.error("Dosya YAML formatında değil", path=file_path)
                return None
            
            # YAML dosyasını oku
            with open(scenario_path, 'r', encoding='utf-8') as f:
                raw_data = yaml.safe_load(f)
            
            if not raw_data:
                logger.error("YAML dosyası boş", path=file_path)
                return None
            
            # Pydantic model ile validate et
            scenario = Scenario(**raw_data)
            
            logger.info("Scenario başarıyla yüklendi", 
                       path=file_path,
                       name=scenario.name,
                       steps_count=len(scenario.steps))
            
            return scenario
            
        except yaml.YAMLError as e:
            logger.error("YAML parse hatası", path=file_path, error=str(e))
            return None
        
        except ValidationError as e:
            logger.error("Scenario validation hatası", 
                        path=file_path, 
                        validation_errors=e.errors())
            return None
        
        except Exception as e:
            logger.error("Scenario yükleme hatası", path=file_path, error=str(e))
            return None
    
    @staticmethod
    def load_scenarios_from_directory(directory: str) -> List[Scenario]:
        """
        Dizindeki tüm YAML dosyalarını scenario olarak yükler
        
        Args:
            directory: Test dizini yolu
            
        Returns:
            Başarıyla yüklenen scenario listesi
        """
        scenarios = []
        test_dir = Path(directory)
        
        if not test_dir.exists():
            logger.error("Test dizini bulunamadı", directory=directory)
            return scenarios
        
        # YAML dosyalarını bul
        yaml_files = list(test_dir.glob("*.yaml")) + list(test_dir.glob("*.yml"))
        
        logger.info("YAML dosyaları bulundu", 
                   directory=directory, 
                   file_count=len(yaml_files))
        
        for yaml_file in yaml_files:
            scenario = YamlLoader.load_scenario(str(yaml_file))
            if scenario:
                scenarios.append(scenario)
        
        logger.info("Scenariolar yüklendi", 
                   total_files=len(yaml_files),
                   loaded_scenarios=len(scenarios))
        
        return scenarios
    
    @staticmethod
    def validate_scenario_syntax(file_path: str) -> Dict[str, Any]:
        """
        YAML dosyasının syntax'ını kontrol eder (yüklemeden)
        
        Args:
            file_path: YAML dosya yolu
            
        Returns:
            Validation sonuçları
        """
        result = {
            "valid": False,
            "errors": [],
            "warnings": []
        }
        
        try:
            scenario_path = Path(file_path)
            
            if not scenario_path.exists():
                result["errors"].append("Dosya bulunamadı")
                return result
            
            # YAML syntax kontrolü
            with open(scenario_path, 'r', encoding='utf-8') as f:
                raw_data = yaml.safe_load(f)
            
            if not raw_data:
                result["errors"].append("YAML dosyası boş")
                return result
            
            # Basic structure kontrolü
            if not isinstance(raw_data, dict):
                result["errors"].append("YAML root object dict olmalı")
                return result
            
            if 'steps' not in raw_data:
                result["errors"].append("'steps' alanı gerekli")
                return result
            
            if not isinstance(raw_data['steps'], list):
                result["errors"].append("'steps' array olmalı")
                return result
            
            if len(raw_data['steps']) == 0:
                result["warnings"].append("Steps listesi boş")
            
            # Pydantic validation
            try:
                scenario = Scenario(**raw_data)
                result["valid"] = True
                result["scenario_name"] = scenario.name
                result["steps_count"] = len(scenario.steps)
                
            except ValidationError as e:
                result["errors"].extend([f"Validation: {err['msg']}" for err in e.errors()])
                return result
            
        except yaml.YAMLError as e:
            result["errors"].append(f"YAML syntax hatası: {str(e)}")
        except Exception as e:
            result["errors"].append(f"Beklenmeyen hata: {str(e)}")
        
        return result
    
    @staticmethod
    def create_example_scenario(output_path: str) -> bool:
        """
        Örnek YAML scenario dosyası oluşturur
        
        Args:
            output_path: Çıktı dosyası yolu
            
        Returns:
            Başarı durumu
        """
        example_scenario = {
            "name": "Örnek Test Senaryosu",
            "description": "Bu bir örnek test senaryosudur",
            "browser": "chromium",
            "headless": True,
            "timeout": 30000,
            "steps": [
                {"goto": "https://example.com"},
                {"fill": {"label": "Username", "value": "test_user"}},
                {"fill": {"label": "Password", "value": "test_pass"}},
                {"click": {"text": "Login"}},
                {"assert_url_not_contains": "login"},
                {"screenshot": {"name": "login_success", "full_page": False}},
                {"click": {"text": "Dashboard"}},
                {"wait": {"seconds": 2}},
                {"assert_url_contains": "dashboard"}
            ]
        }
        
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                yaml.dump(example_scenario, f, 
                         default_flow_style=False, 
                         allow_unicode=True,
                         indent=2)
            
            logger.info("Örnek scenario oluşturuldu", path=output_path)
            return True
            
        except Exception as e:
            logger.error("Örnek scenario oluşturulamadı", path=output_path, error=str(e))
            return False

# Module-level convenience functions
def load_scenario(file_path: str) -> Optional[Scenario]:
    """Convenience function for loading a scenario"""
    return YamlLoader.load_scenario(file_path)

def load_scenarios_from_directory(directory: str) -> List[Scenario]:
    """Convenience function for loading scenarios from directory"""
    return YamlLoader.load_scenarios_from_directory(directory)

def validate_scenario_syntax(file_path: str) -> Dict[str, Any]:
    """Convenience function for validating scenario syntax"""
    return YamlLoader.validate_scenario_syntax(file_path)

def create_example_scenario(output_path: str) -> bool:
    """Convenience function for creating example scenario"""
    return YamlLoader.create_example_scenario(output_path) 