#!/usr/bin/env python3
"""
AI角色系统 - 测试执行器

执行18个测试任务，验证角色系统的完整工作流。
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import sys

# 添加core目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'core'))

from role_loader import RoleLoader
from rule_engine import RuleEngine
from model_router import ModelRouter, TaskComplexity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """测试结果"""
    task_id: str
    task_name: str
    status: str  # success, failed, error
    duration: float  # seconds
    selected_model: str
    estimated_cost: float
    steps_completed: int
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'status': self.status,
            'duration': self.duration,
            'selected_model': self.selected_model,
            'estimated_cost': self.estimated_cost,
            'steps_completed': self.steps_completed,
            'error_message': self.error_message,
            'details': self.details
        }


class TestRunner:
    """测试执行器核心"""

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化测试执行器

        Args:
            base_path: ai-role-system目录路径
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = Path(base_path)
        self.test_framework_dir = self.base_path / 'test-suite'

        if not self.test_framework_dir.exists():
            raise ValueError(f"Test suite directory not found: {self.test_framework_dir}")

        # 初始化组件
        self.role_loader = RoleLoader(base_path)
        self.rule_engine = RuleEngine(base_path)
        self.model_router = ModelRouter(base_path)

        # 加载测试定义
        self.task_definitions = self._load_yaml('task-definitions.yaml')
        self.evaluation_metrics = self._load_yaml('evaluation-metrics.yaml')

        # 测试结果
        self.results: List[TestResult] = []

        logger.info("TestRunner initialized")

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """加载YAML配置文件"""
        file_path = self.test_framework_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Error loading {filename}: {e}")

    def get_tasks(self) -> List[Dict[str, Any]]:
        """获取所有测试任务"""
        # task_definitions的结构是: test_tasks -> {analyst_tasks: [...], architect_tasks: [...]}
        test_tasks = self.task_definitions.get('test_tasks', {})
        all_tasks = []

        # 遍历所有角色分组，合并任务列表
        for role_group, tasks in test_tasks.items():
            if isinstance(tasks, list):
                all_tasks.extend(tasks)

        return all_tasks

    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取测试任务"""
        for task in self.get_tasks():
            if task.get('id') == task_id:
                return task
        return None

    def run_task(self, task_id: str) -> TestResult:
        """
        执行单个测试任务

        Args:
            task_id: 测试任务ID

        Returns:
            测试结果
        """
        task = self.get_task_by_id(task_id)
        if not task:
            return TestResult(
                task_id=task_id,
                task_name="Unknown",
                status="error",
                duration=0.0,
                selected_model="none",
                estimated_cost=0.0,
                steps_completed=0,
                error_message=f"Task {task_id} not found"
            )

        logger.info(f"Running task: {task_id} - {task.get('name')}")
        start_time = datetime.now()

        try:
            # 1. 确定任务复杂度
            complexity_str = task.get('complexity', 'medium')
            complexity = self._parse_complexity(complexity_str)

            # 2. 模型路由决策
            task_type = task.get('type', 'general')
            routing_decision = self.model_router.route(
                task_type=task_type,
                complexity=complexity,
                context_size=task.get('estimated_context', 5000)
            )

            # 3. 加载相关角色
            roles_needed = task.get('roles', [])
            roles = {role_id: self.role_loader.load_role(role_id) for role_id in roles_needed}

            # 4. 检查规则
            scope = task.get('scope', 'backend')
            blocking_violations = self.rule_engine.check_blocking_rules(
                scope=scope,
                context={'operation': task_type, 'check_violations': False}
            )

            # 5. 模拟工作流执行
            steps_completed = self._simulate_workflow(task, roles)

            # 6. 计算耗时
            duration = (datetime.now() - start_time).total_seconds()

            # 7. 创建结果
            result = TestResult(
                task_id=task_id,
                task_name=task.get('name', 'Unknown'),
                status="success",
                duration=duration,
                selected_model=routing_decision.selected_model,
                estimated_cost=routing_decision.estimated_cost,
                steps_completed=steps_completed,
                details={
                    'complexity': complexity_str,
                    'roles_used': list(roles.keys()),
                    'blocking_violations': len(blocking_violations),
                    'routing_confidence': routing_decision.confidence
                }
            )

            self.results.append(result)
            logger.info(f"Task {task_id} completed: {result.status}")
            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            result = TestResult(
                task_id=task_id,
                task_name=task.get('name', 'Unknown'),
                status="error",
                duration=duration,
                selected_model="none",
                estimated_cost=0.0,
                steps_completed=0,
                error_message=str(e)
            )
            self.results.append(result)
            logger.error(f"Task {task_id} failed: {e}")
            return result

    def _parse_complexity(self, complexity_str: str) -> TaskComplexity:
        """解析复杂度字符串"""
        mapping = {
            'simple': TaskComplexity.SIMPLE,
            'medium': TaskComplexity.MEDIUM,
            'complex': TaskComplexity.COMPLEX
        }
        return mapping.get(complexity_str.lower(), TaskComplexity.MEDIUM)

    def _simulate_workflow(self, task: Dict[str, Any], roles: Dict[str, Dict]) -> int:
        """
        模拟工作流执行

        Args:
            task: 任务定义
            roles: 角色配置字典

        Returns:
            完成的步骤数
        """
        # 简化实现：计算工作流步骤数
        steps = 0
        for role_id, role_config in roles.items():
            workflow_steps = role_config.get('workflow', [])
            steps += len(workflow_steps)

        return steps

    def run_all_tasks(self, task_ids: Optional[List[str]] = None) -> List[TestResult]:
        """
        执行所有测试任务（或指定的任务列表）

        Args:
            task_ids: 要执行的任务ID列表，None表示执行所有任务

        Returns:
            测试结果列表
        """
        tasks = self.get_tasks()

        if task_ids:
            tasks = [t for t in tasks if t.get('id') in task_ids]

        logger.info(f"Running {len(tasks)} tasks...")

        results = []
        for task in tasks:
            task_id = task.get('id')
            result = self.run_task(task_id)
            results.append(result)

        return results

    def generate_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        生成测试报告

        Args:
            output_path: 报告输出路径

        Returns:
            报告数据字典
        """
        if not self.results:
            logger.warning("No test results to report")
            return {}

        # 统计数据
        total = len(self.results)
        success = sum(1 for r in self.results if r.status == "success")
        failed = sum(1 for r in self.results if r.status == "failed")
        error = sum(1 for r in self.results if r.status == "error")
        total_cost = sum(r.estimated_cost for r in self.results)
        total_duration = sum(r.duration for r in self.results)

        report = {
            'summary': {
                'total_tasks': total,
                'success': success,
                'failed': failed,
                'error': error,
                'success_rate': f"{(success/total*100):.1f}%" if total > 0 else "0%",
                'total_cost': f"${total_cost:.4f}",
                'total_duration': f"{total_duration:.2f}s"
            },
            'results': [r.to_dict() for r in self.results],
            'timestamp': datetime.now().isoformat()
        }

        # 写入文件
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(report, f, allow_unicode=True, default_flow_style=False)

            logger.info(f"Report saved to: {output_path}")

        return report

    def clear_results(self):
        """清空测试结果"""
        self.results.clear()
        logger.info("Test results cleared")


# 便捷函数
def create_runner(base_path: Optional[Path] = None) -> TestRunner:
    """创建测试执行器实例"""
    return TestRunner(base_path)


if __name__ == '__main__':
    # 测试代码
    runner = TestRunner()

    print("=== 测试执行器验证 ===\n")

    # 测试1: 加载测试任务
    print("1. 加载测试任务:")
    tasks = runner.get_tasks()
    print(f"   Total tasks: {len(tasks)}")
    if tasks:
        print(f"   First task: {tasks[0].get('id')} - {tasks[0].get('name')}")

    # 测试2: 执行单个测试任务
    print("\n2. 执行单个测试任务:")
    if tasks:
        first_task_id = tasks[0].get('id')
        result = runner.run_task(first_task_id)
        print(f"   Task: {result.task_name}")
        print(f"   Status: {result.status}")
        print(f"   Model: {result.selected_model}")
        print(f"   Cost: ${result.estimated_cost:.4f}")
        print(f"   Duration: {result.duration:.3f}s")

    # 测试3: 生成报告
    print("\n3. 生成测试报告:")
    report = runner.generate_report()
    if report:
        print(f"   Summary: {report['summary']}")

    print("\n✅ 测试执行器验证完成")



