"""
Verifier Agent
Test sonuçlarını doğrular ve raporlar.
"""

from typing import Dict, Any, List
import structlog
from datetime import datetime
from pathlib import Path

logger = structlog.get_logger(__name__)


class VerifierAgent:
    """
    Test doğrulama ve raporlamadan sorumlu agent
    - Test execution sonuçlarını analiz eder
    - Assertion'ları kontrol eder
    - Test raporları oluşturur
    - Hata durumlarında detaylı analiz yapar
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini"):
        self.logger = logger.bind(agent="verifier")
        self.llm_model = llm_model
    
    def verify_test_results_tool(self, execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test execution sonuçlarını doğrular
        
        Args:
            execution_results: Executor'dan gelen sonuçlar
            
        Returns:
            Verification sonuçları
        """
        self.logger.info("Test sonuçları doğrulanıyor", 
                        total_steps=len(execution_results.get("steps", [])))
        
        verification = {
            "overall_status": "unknown",
            "total_steps": 0,
            "passed_steps": 0,
            "failed_steps": 0,
            "skipped_steps": 0,
            "success_rate": 0.0,
            "critical_failures": [],
            "warnings": [],
            "test_quality_score": 0.0
        }
        
        steps = execution_results.get("steps", [])
        verification["total_steps"] = len(steps)
        
        for step_result in steps:
            status = step_result.get("status", "unknown")
            
            if status == "success":
                verification["passed_steps"] += 1
            elif status == "error":
                verification["failed_steps"] += 1
                
                # Critical failure kontrolü
                if self._is_critical_failure(step_result):
                    verification["critical_failures"].append({
                        "step_index": step_result.get("step_index"),
                        "error": step_result.get("error"),
                        "error_type": step_result.get("error_type"),
                        "impact": "critical"
                    })
            else:
                verification["skipped_steps"] += 1
        
        # Success rate hesaplama
        if verification["total_steps"] > 0:
            verification["success_rate"] = verification["passed_steps"] / verification["total_steps"]
        
        # Overall status belirleme
        if verification["success_rate"] == 1.0:
            verification["overall_status"] = "passed"
        elif verification["success_rate"] >= 0.8:
            verification["overall_status"] = "passed_with_warnings"
        elif verification["success_rate"] >= 0.5:
            verification["overall_status"] = "partially_failed"
        else:
            verification["overall_status"] = "failed"
        
        # Test kalite skoru hesaplama
        verification["test_quality_score"] = self._calculate_quality_score(verification, steps)
        
        # Warning'leri tespit et
        verification["warnings"] = self._detect_warnings(steps, verification)
        
        self.logger.info("Verification tamamlandı",
                        status=verification["overall_status"],
                        success_rate=verification["success_rate"],
                        quality_score=verification["test_quality_score"])
        
        return verification
    
    def generate_test_report_tool(self, 
                                 scenario_data: Dict[str, Any],
                                 execution_results: Dict[str, Any], 
                                 verification_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Kapsamlı test raporu oluşturur
        
        Args:
            scenario_data: Orijinal YAML scenario
            execution_results: Execution sonuçları
            verification_results: Verification sonuçları
            
        Returns:
            Test raporu
        """
        self.logger.info("Test raporu oluşturuluyor")
        
        report_timestamp = datetime.now().isoformat()
        
        report = {
            "metadata": {
                "test_name": scenario_data.get("name", "Unnamed Test"),
                "timestamp": report_timestamp,
                "duration": execution_results.get("total_duration", 0),
                "browser": scenario_data.get("browser", "chromium"),
                "headless": scenario_data.get("headless", True)
            },
            "summary": {
                "overall_status": verification_results["overall_status"],
                "total_steps": verification_results["total_steps"],
                "passed": verification_results["passed_steps"],
                "failed": verification_results["failed_steps"],
                "success_rate": verification_results["success_rate"],
                "quality_score": verification_results["test_quality_score"]
            },
            "step_details": [],
            "failures": verification_results.get("critical_failures", []),
            "warnings": verification_results.get("warnings", []),
            "recommendations": [],
            "artifacts": {
                "screenshots": [],
                "traces": [],
                "logs": []
            }
        }
        
        # Step detaylarını ekle
        steps = execution_results.get("steps", [])
        for i, step_result in enumerate(steps):
            step_detail = {
                "index": i,
                "action": step_result.get("action", "unknown"),
                "status": step_result.get("status", "unknown"),
                "duration": step_result.get("duration", 0),
                "target": step_result.get("target") or step_result.get("url") or "N/A"
            }
            
            if step_result.get("status") == "error":
                step_detail["error"] = step_result.get("error")
                step_detail["error_type"] = step_result.get("error_type")
            
            report["step_details"].append(step_detail)
        
        # Önerileri oluştur
        report["recommendations"] = self._generate_recommendations(
            verification_results, execution_results, scenario_data
        )
        
        # Artifact'leri topla
        report["artifacts"] = self._collect_artifacts(execution_results)
        
        self.logger.info("Test raporu oluşturuldu", 
                        report_status=report["summary"]["overall_status"])
        
        return report
    
    def analyze_failures_tool(self, failure_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Hata detaylarını analiz eder ve pattern'leri tespit eder
        
        Args:
            failure_data: Hata verileri listesi
            
        Returns:
            Failure analizi
        """
        self.logger.info("Hata analizi yapılıyor", failure_count=len(failure_data))
        
        analysis = {
            "failure_patterns": {},
            "root_causes": [],
            "fix_suggestions": [],
            "impact_assessment": "low"
        }
        
        if not failure_data:
            return analysis
        
        # Hata pattern'lerini grupla
        error_types = {}
        for failure in failure_data:
            error_type = failure.get("error_type", "unknown")
            if error_type not in error_types:
                error_types[error_type] = []
            error_types[error_type].append(failure)
        
        analysis["failure_patterns"] = error_types
        
        # Root cause analizi
        for error_type, failures in error_types.items():
            if error_type == "timeout":
                analysis["root_causes"].append("Sayfa yüklenme süreleri yavaş olabilir")
                analysis["fix_suggestions"].append("Timeout değerlerini artır veya wait stratejisi ekle")
            elif error_type == "element_not_found":
                analysis["root_causes"].append("DOM değişiklikleri veya zayıf selector'lar")
                analysis["fix_suggestions"].append("Daha güçlü selector'lar kullan veya wait condition ekle")
            elif error_type == "navigation_failed":
                analysis["root_causes"].append("Network connectivity veya server sorunları")
                analysis["fix_suggestions"].append("Network retry policy ekle")
        
        # Impact assessment
        total_failures = len(failure_data)
        if total_failures >= 3:
            analysis["impact_assessment"] = "high"
        elif total_failures >= 2:
            analysis["impact_assessment"] = "medium"
        
        return analysis
    
    def validate_assertions_tool(self, assertion_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assertion sonuçlarını detaylı olarak doğrular
        
        Args:
            assertion_results: Assertion step sonuçları
            
        Returns:
            Assertion validation sonuçları
        """
        self.logger.info("Assertion'lar doğrulanıyor", count=len(assertion_results))
        
        validation = {
            "total_assertions": len(assertion_results),
            "passed_assertions": 0,
            "failed_assertions": 0,
            "assertion_details": [],
            "confidence_score": 1.0
        }
        
        for assertion in assertion_results:
            detail = {
                "type": assertion.get("action", "unknown"),
                "expected": assertion.get("fragment"),
                "actual": assertion.get("current_url"),
                "passed": assertion.get("passed", False),
                "confidence": 1.0
            }
            
            if detail["passed"]:
                validation["passed_assertions"] += 1
            else:
                validation["failed_assertions"] += 1
                # Failed assertion'lar için confidence düşür
                validation["confidence_score"] *= 0.8
            
            validation["assertion_details"].append(detail)
        
        return validation
    
    def _is_critical_failure(self, step_result: Dict[str, Any]) -> bool:
        """Step failure'ının critical olup olmadığını belirler"""
        error_type = step_result.get("error_type", "")
        action = step_result.get("action", "")
        
        # Assertion failure'ları her zaman critical
        if action.startswith("assert"):
            return True
        
        # Navigation failure'ları critical
        if error_type == "navigation_failed":
            return True
        
        return False
    
    def _calculate_quality_score(self, verification: Dict[str, Any], steps: List[Dict[str, Any]]) -> float:
        """Test kalite skorunu hesaplar"""
        base_score = verification["success_rate"]
        
        # Critical failure penalty
        critical_count = len(verification["critical_failures"])
        critical_penalty = critical_count * 0.2
        
        # Step çeşitliliği bonusu
        action_types = set()
        for step in steps:
            action_types.add(step.get("action", "unknown"))
        
        diversity_bonus = min(len(action_types) * 0.1, 0.3)
        
        quality_score = max(0.0, min(1.0, base_score - critical_penalty + diversity_bonus))
        
        return round(quality_score, 2)
    
    def _detect_warnings(self, steps: List[Dict[str, Any]], verification: Dict[str, Any]) -> List[str]:
        """Test execution'da warning'leri tespit eder"""
        warnings = []
        
        # Yavaş step'ler
        slow_steps = [s for s in steps if s.get("duration", 0) > 5.0]
        if slow_steps:
            warnings.append(f"{len(slow_steps)} adım 5 saniyeden uzun sürdü")
        
        # Success rate uyarıları
        if 0.8 <= verification["success_rate"] < 1.0:
            warnings.append("Test başarı oranı ideal seviyenin altında")
        
        # Çok fazla retry
        retry_count = sum(1 for s in steps if "retry" in str(s.get("error", "")))
        if retry_count > 2:
            warnings.append("Çok fazla retry gerekti, test stability problemi olabilir")
        
        return warnings
    
    def _generate_recommendations(self, verification: Dict[str, Any], 
                                execution: Dict[str, Any], 
                                scenario: Dict[str, Any]) -> List[str]:
        """Test iyileştirme önerileri oluşturur"""
        recommendations = []
        
        # Success rate bazlı öneriler
        if verification["success_rate"] < 0.8:
            recommendations.append("Test stability'sini artırmak için wait strategy'leri ekleyin")
        
        # Performance önerileri
        total_duration = execution.get("total_duration", 0)
        step_count = verification["total_steps"]
        if step_count > 0 and (total_duration / step_count) > 3.0:
            recommendations.append("Test performance'ını artırmak için paralel execution düşünün")
        
        # Maintenance önerileri
        if len(verification["critical_failures"]) > 0:
            recommendations.append("Critical failure'ları önlemek için selector'ları güçlendirin")
        
        return recommendations
    
    def _collect_artifacts(self, execution_results: Dict[str, Any]) -> Dict[str, List[str]]:
        """Test artifact'lerini toplar"""
        artifacts = {
            "screenshots": [],
            "traces": [],
            "logs": []
        }
        
        # Screenshot dosyalarını bul
        screenshots_dir = Path("screenshots")
        if screenshots_dir.exists():
            artifacts["screenshots"] = [str(f) for f in screenshots_dir.glob("*.png")]
        
        # Trace dosyalarını bul
        traces_dir = Path("traces")
        if traces_dir.exists():
            artifacts["traces"] = [str(f) for f in traces_dir.glob("*.zip")]
        
        # Log dosyalarını bul
        logs_dir = Path("logs")
        if logs_dir.exists():
            artifacts["logs"] = [str(f) for f in logs_dir.glob("*.log")]
        
        return artifacts 