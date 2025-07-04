"""
Crew Manager
Tüm agent'ları orkestra eder ve test execution workflow'unu yönetir.
"""

from typing import Dict, Any, Optional
import structlog
import yaml
from pathlib import Path
from datetime import datetime

from .planner import PlannerAgent
from .executor import ExecutorAgent
from .verifier import VerifierAgent

logger = structlog.get_logger(__name__)


class CrewManager:
    """
    Test automation crew'unu yönetir
    - Agent'ları koordine eder
    - Task flow'unu kontrol eder  
    - Error recovery süreçlerini yönetir
    - Sonuçları toplar ve raporlar
    """
    
    def __init__(self, llm_model: str = "gpt-4o-mini", headless: bool = True):
        self.logger = logger.bind(component="crew_manager")
        self.llm_model = llm_model
        self.headless = headless
        
        # Agent'ları başlat
        self.planner = PlannerAgent(llm_model=llm_model)
        self.executor = ExecutorAgent(llm_model=llm_model, headless=headless)
        self.verifier = VerifierAgent(llm_model=llm_model)
    
    async def run_scenario(self, scenario_path: str) -> Dict[str, Any]:
        """
        YAML test senaryosunu çalıştırır
        
        Args:
            scenario_path: YAML dosya yolu
            
        Returns:
            Toplam test sonuçları
        """
        self.logger.info("Test senaryosu çalıştırılıyor", scenario_path=scenario_path)
        
        # YAML dosyasını yükle
        scenario_data = self._load_scenario(scenario_path)
        if not scenario_data:
            return {"status": "error", "message": "Scenario yüklenemedi"}
        
        # Execution context oluştur
        execution_context = {
            "scenario_path": scenario_path,
            "scenario_data": scenario_data,
            "start_time": datetime.now(),
            "status": "running"
        }
        
        try:
            # 1. PLANNING PHASE
            self.logger.info("Planning fazı başlıyor")
            planning_result = await self._run_planning_phase(scenario_data, execution_context)
            
            if planning_result["status"] != "success":
                return {"status": "planning_failed", "error": planning_result.get("error")}
            
            # 2. EXECUTION PHASE  
            self.logger.info("Execution fazı başlıyor")
            execution_result = await self._run_execution_phase(scenario_data, planning_result, execution_context)
            
            # 3. VERIFICATION PHASE
            self.logger.info("Verification fazı başlıyor")
            verification_result = await self._run_verification_phase(scenario_data, execution_result, execution_context)
            
            # 4. FINALIZATION
            final_result = self._finalize_results(scenario_data, execution_result, verification_result, execution_context)
            
            self.logger.info("Test senaryosu tamamlandı", 
                           status=final_result["summary"]["overall_status"],
                           duration=final_result["metadata"]["duration"])
            
            return final_result
            
        except Exception as e:
            self.logger.error("Test execution hatası", error=str(e))
            return {
                "status": "error",
                "error": str(e),
                "context": execution_context
            }
    
    async def _run_planning_phase(self, scenario_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Planning fazını çalıştırır"""
        
        try:
            # Analysis çalıştır
            analysis_result = self.planner.analyze_scenario_tool(scenario_data)
            context["analysis"] = analysis_result
            
            # Plan oluştur
            execution_plan = self.planner.create_execution_plan_tool(scenario_data, analysis_result)
            context["execution_plan"] = execution_plan
            
            return {
                "status": "success",
                "analysis": analysis_result,
                "execution_plan": execution_plan
            }
            
        except Exception as e:
            self.logger.error("Planning fazı hatası", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _run_execution_phase(self, 
                                 scenario_data: Dict[str, Any], 
                                 planning_result: Dict[str, Any],
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Execution fazını çalıştırır"""
        
        execution_plan = planning_result["execution_plan"]
        steps = scenario_data.get("steps", [])
        
        # Browser'ı başlat
        browser_config = {
            "browser": scenario_data.get("browser", "chromium"),
            "headless": scenario_data.get("headless", self.headless),
            "timeout": scenario_data.get("timeout", 30000)
        }
        
        init_result = self.executor.initialize_browser_tool(browser_config)
        if init_result["status"] != "success":
            return {"status": "browser_init_failed", "error": init_result["message"]}
        
        # Step'leri çalıştır
        step_results = []
        total_duration = 0.0
        
        for i, step in enumerate(steps):
            step_start = datetime.now()
            
            try:
                self.logger.info("Step çalıştırılıyor", step_index=i, step=step)
                
                # Step'i çalıştır
                step_result = self.executor.execute_step_tool(step, i)
                step_result["duration"] = (datetime.now() - step_start).total_seconds()
                total_duration += step_result["duration"]
                
                step_results.append(step_result)
                
                # Hata durumunda recovery
                if step_result["status"] == "error":
                    recovery_result = await self._handle_step_failure(step, step_result, planning_result, context)
                    
                    if recovery_result["status"] == "recovered":
                        # Recovery başarılı, devam et
                        step_result.update(recovery_result)
                    elif recovery_result["status"] == "abort":
                        # Test'i durdur
                        self.logger.warning("Test aborting due to critical failure", step_index=i)
                        break
                
            except Exception as e:
                self.logger.error("Step execution exception", step_index=i, error=str(e))
                step_results.append({
                    "status": "error",
                    "step_index": i,
                    "error": str(e),
                    "duration": (datetime.now() - step_start).total_seconds()
                })
        
        # Browser'ı kapat
        self.executor.close_browser_tool()
        
        return {
            "status": "completed",
            "steps": step_results,
            "total_duration": total_duration,
            "browser_config": browser_config
        }
    
    async def _run_verification_phase(self,
                                    scenario_data: Dict[str, Any],
                                    execution_result: Dict[str, Any], 
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        """Verification fazını çalıştırır"""
        
        try:
            # Test sonuçlarını doğrula
            verification_result = self.verifier.verify_test_results_tool(execution_result)
            
            # Assertion'ları ayrıca kontrol et
            assertion_steps = [s for s in execution_result["steps"] if s.get("action", "").startswith("assert")]
            if assertion_steps:
                assertion_validation = self.verifier.validate_assertions_tool(assertion_steps)
                verification_result["assertion_validation"] = assertion_validation
            
            # Failure analizi
            failed_steps = [s for s in execution_result["steps"] if s.get("status") == "error"]
            if failed_steps:
                failure_analysis = self.verifier.analyze_failures_tool(failed_steps)
                verification_result["failure_analysis"] = failure_analysis
            
            # Test raporu oluştur
            test_report = self.verifier.generate_test_report_tool(
                scenario_data, execution_result, verification_result
            )
            
            return {
                "status": "success",
                "verification": verification_result,
                "report": test_report
            }
            
        except Exception as e:
            self.logger.error("Verification fazı hatası", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _handle_step_failure(self,
                                 failed_step: Dict[str, Any],
                                 step_result: Dict[str, Any], 
                                 planning_result: Dict[str, Any],
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Step failure durumunda recovery yönetir"""
        
        self.logger.warning("Step failure detected, attempting recovery", 
                          step_index=step_result.get("step_index"),
                          error_type=step_result.get("error_type"))
        
        # Recovery planı oluştur
        error_context = {
            "error_type": step_result.get("error_type"),
            "failed_step": failed_step,
            "step_index": step_result.get("step_index"),
            "error_message": step_result.get("error")
        }
        
        recovery_plan = self.planner.suggest_recovery_plan_tool(error_context)
        
        # Recovery strategy'ye göre aksiyon al
        strategy = recovery_plan.get("strategy", "skip")
        
        if strategy == "retry_with_fallback":
            # Basit retry dene
            for attempt in range(recovery_plan.get("max_attempts", 2)):
                self.logger.info("Recovery attempt", attempt=attempt + 1)
                
                retry_result = self.executor.execute_step_tool(failed_step, step_result["step_index"])
                
                if retry_result["status"] == "success":
                    return {
                        "status": "recovered",
                        "recovery_method": "retry",
                        "attempts": attempt + 1
                    }
            
            return {"status": "abort", "reason": "Max retry attempts exceeded"}
        
        elif strategy == "skip":
            return {
                "status": "recovered", 
                "recovery_method": "skip",
                "warning": "Step skipped due to failure"
            }
        
        else:
            return {"status": "abort", "reason": "No recovery strategy available"}
    
    def _load_scenario(self, scenario_path: str) -> Optional[Dict[str, Any]]:
        """YAML scenario dosyasını yükler"""
        try:
            scenario_file = Path(scenario_path)
            if not scenario_file.exists():
                self.logger.error("Scenario dosyası bulunamadı", path=scenario_path)
                return None
            
            with open(scenario_file, 'r', encoding='utf-8') as f:
                scenario_data = yaml.safe_load(f)
            
            self.logger.info("Scenario yüklendi", path=scenario_path, steps=len(scenario_data.get("steps", [])))
            return scenario_data
            
        except Exception as e:
            self.logger.error("Scenario yükleme hatası", path=scenario_path, error=str(e))
            return None
    
    def _finalize_results(self,
                         scenario_data: Dict[str, Any],
                         execution_result: Dict[str, Any],
                         verification_result: Dict[str, Any], 
                         context: Dict[str, Any]) -> Dict[str, Any]:
        """Final sonuçları derler"""
        
        end_time = datetime.now()
        start_time = context["start_time"]
        total_duration = (end_time - start_time).total_seconds()
        
        return {
            "metadata": {
                "scenario_name": scenario_data.get("name", "Unnamed Scenario"),
                "scenario_path": context["scenario_path"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration": total_duration
            },
            "summary": verification_result["report"]["summary"],
            "execution": execution_result,
            "verification": verification_result["verification"],
            "report": verification_result["report"],
            "context": context
        } 