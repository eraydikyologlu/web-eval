"""
Planner Agent
Test senaryolarını analiz eder ve execution planı oluşturur.
"""

from typing import List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class PlannerAgent:
    """
    Test planlamadan sorumlu agent
    - YAML senaryosunu analiz eder
    - Risk alanlarını belirler  
    - Alternatif stratejiler önerir
    - Hata durumunda yeni plan oluşturur
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini"):
        self.logger = logger.bind(agent="planner")
        self.llm_model = llm_model
    
    def analyze_scenario_tool(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        YAML test senaryosunu analiz eder ve risk değerlendirmesi yapar
        
        Args:
            scenario_data: Parsed YAML scenario data
            
        Returns:
            Analysis sonuçları ve öneriler
        """
        self.logger.info("Senaryo analizi başlıyor", steps_count=len(scenario_data.get("steps", [])))
        
        analysis = {
            "total_steps": len(scenario_data.get("steps", [])),
            "risk_areas": [],
            "complexity_score": 0,
            "estimated_duration": 0,
            "recommendations": []
        }
        
        steps = scenario_data.get("steps", [])
        
        for i, step in enumerate(steps):
            step_risk = self._assess_step_risk(step, i)
            if step_risk["risk_level"] > 2:
                analysis["risk_areas"].append({
                    "step_index": i,
                    "step_data": step,
                    "risks": step_risk["risks"],
                    "mitigation": step_risk["mitigation"]
                })
            
            analysis["complexity_score"] += step_risk["complexity"]
            analysis["estimated_duration"] += step_risk["duration"]
        
        # Genel öneriler
        if analysis["complexity_score"] > 15:
            analysis["recommendations"].append("Senaryoyu daha küçük parçalara böl")
        
        if len([s for s in steps if "fill" in s]) > 5:
            analysis["recommendations"].append("Form step'lerini batch'le, page loading'e dikkat et")
            
        self.logger.info("Senaryo analizi tamamlandı", 
                        complexity=analysis["complexity_score"],
                        risk_count=len(analysis["risk_areas"]))
        
        return analysis
    
    def create_execution_plan_tool(self, scenario_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiz sonuçlarına göre execution planı oluşturur
        
        Args:
            scenario_data: YAML scenario
            analysis: Analiz sonuçları
            
        Returns:
            Detaylı execution planı
        """
        self.logger.info("Execution planı oluşturuluyor")
        
        plan = {
            "execution_strategy": "sequential",  # sequential, parallel, batch
            "timeout_strategy": "adaptive",      # fixed, adaptive, aggressive  
            "retry_strategy": "smart",           # simple, smart, progressive
            "checkpoints": [],                   # İyileştirme noktaları
            "recovery_points": [],               # Hata recovery noktaları
            "parallel_groups": []                # Paralel çalıştırılabilir step grupları
        }
        
        # Risk alanları için checkpoint'ler oluştur
        for risk_area in analysis.get("risk_areas", []):
            checkpoint = {
                "before_step": risk_area["step_index"],
                "type": "verification",
                "action": "screenshot",
                "validation": risk_area["mitigation"]
            }
            plan["checkpoints"].append(checkpoint)
        
        # Recovery point'leri belirle
        steps = scenario_data.get("steps", [])
        for i, step in enumerate(steps):
            if "assert" in str(step) or i == len(steps) - 1:
                plan["recovery_points"].append({
                    "step_index": i,
                    "type": "assertion_point",
                    "fallback_action": "retry_from_last_checkpoint"
                })
        
        self.logger.info("Execution planı oluşturuldu", 
                        checkpoints=len(plan["checkpoints"]),
                        recovery_points=len(plan["recovery_points"]))
        
        return plan
    
    def suggest_recovery_plan_tool(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Hata durumunda recovery planı önerir
        
        Args:
            error_context: Hata bilgileri ve context
            
        Returns:
            Recovery planı
        """
        self.logger.warning("Recovery planı oluşturuluyor", error=error_context.get("error_type"))
        
        recovery_plan = {
            "strategy": "retry_with_fallback",
            "max_attempts": 3,
            "fallback_actions": [],
            "alternative_selectors": [],
            "skip_conditions": []
        }
        
        error_type = error_context.get("error_type", "unknown")
        failed_step = error_context.get("failed_step", {})
        
        if error_type == "timeout":
            recovery_plan["fallback_actions"].extend([
                {"type": "wait", "duration": 2},
                {"type": "scroll_to_element"},
                {"type": "retry_step"}
            ])
        elif error_type == "element_not_found":
            recovery_plan["alternative_selectors"] = self._generate_alternative_selectors(failed_step)
        elif error_type == "navigation_failed":
            recovery_plan["fallback_actions"].extend([
                {"type": "refresh_page"},
                {"type": "clear_cookies"},
                {"type": "retry_navigation"}
            ])
        
        return recovery_plan
    
    def _assess_step_risk(self, step: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Step'in risk seviyesini değerlendirir"""
        risk_assessment = {
            "risk_level": 1,  # 1-5 arası
            "complexity": 2,   # 1-10 arası  
            "duration": 1.0,   # saniye
            "risks": [],
            "mitigation": []
        }
        
        # Fill action riskleri
        if "fill" in step:
            fill_data = step["fill"]
            if not fill_data.get("selector") and not fill_data.get("label"):
                risk_assessment["risks"].append("Zayıf element locator")
                risk_assessment["risk_level"] += 1
                risk_assessment["mitigation"].append("Label veya güçlü selector kullan")
        
        # Click action riskleri  
        if "click" in step:
            click_data = step["click"]
            if click_data.get("text") and len(click_data["text"]) < 3:
                risk_assessment["risks"].append("Çok kısa button text")
                risk_assessment["risk_level"] += 1
        
        # Assertion riskleri
        if any(key.startswith("assert") for key in step.keys()):
            risk_assessment["risks"].append("Assertion step - kritik kontrol noktası")
            risk_assessment["complexity"] += 2
        
        return risk_assessment
    
    def _generate_alternative_selectors(self, failed_step: Dict[str, Any]) -> List[str]:
        """Failed step için alternatif selector'lar üretir"""
        alternatives = []
        
        if "click" in failed_step:
            text = failed_step["click"].get("text", "")
            if text:
                alternatives.extend([
                    f"button:has-text('{text}')",
                    f"[aria-label*='{text}']",
                    f"a:has-text('{text}')",
                    f"input[value='{text}']"
                ])
        
        if "fill" in failed_step:
            label = failed_step["fill"].get("label", "")
            if label:
                alternatives.extend([
                    f"input[placeholder*='{label}']",
                    f"label:has-text('{label}') + input",
                    f"[aria-label*='{label}']"
                ])
        
        return alternatives 