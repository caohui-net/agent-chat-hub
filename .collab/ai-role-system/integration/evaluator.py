#!/usr/bin/env python3
"""
AI角色系统 - 评估系统

基于36个评估指标对测试结果进行评分和分析。
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class MetricScore:
    """评估指标得分"""
    metric_id: str
    metric_name: str
    score: float  # 0.0-1.0
    weight: float
    category: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def weighted_score(self) -> float:
        """加权得分"""
        return self.score * self.weight


@dataclass
class EvaluationResult:
    """评估结果"""
    task_id: str
    task_name: str
    overall_score: float
    category_scores: Dict[str, float]
    metric_scores: List[MetricScore]
    pass_status: bool
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'overall_score': self.overall_score,
            'category_scores': self.category_scores,
            'metric_scores': [
                {
                    'metric_id': m.metric_id,
                    'metric_name': m.metric_name,
                    'score': m.score,
                    'weight': m.weight,
                    'category': m.category
                }
                for m in self.metric_scores
            ],
            'pass_status': self.pass_status,
            'timestamp': self.timestamp
        }


class Evaluator:
    """评估系统核心"""

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化评估系统

        Args:
            base_path: ai-role-system目录路径
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = Path(base_path)
        self.test_suite_dir = self.base_path / 'test-suite'

        if not self.test_suite_dir.exists():
            raise ValueError(f"Test suite directory not found: {self.test_suite_dir}")

        # 加载评估指标
        self.evaluation_metrics = self._load_yaml('evaluation-metrics.yaml')
        self.metrics_index = self._build_metrics_index()

        logger.info("Evaluator initialized")

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """加载YAML配置文件"""
        file_path = self.test_suite_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Error loading {filename}: {e}")

    def _build_metrics_index(self) -> Dict[str, Dict[str, Any]]:
        """构建指标索引"""
        index = {}

        # evaluation_metrics的结构: evaluation_metrics -> {role_metrics: {metric_name: {...}}}
        metrics_data = self.evaluation_metrics.get('evaluation_metrics', {})

        for role_category, role_metrics in metrics_data.items():
            if isinstance(role_metrics, dict):
                # 提取类别名（如 analyst_metrics -> analyst）
                category = role_category.replace('_metrics', '')

                for metric_id, metric_config in role_metrics.items():
                    if isinstance(metric_config, dict):
                        # 添加元数据
                        metric_config['id'] = metric_id
                        metric_config['name'] = metric_config.get('description', metric_id)
                        metric_config['category'] = category
                        metric_config['weight'] = 1.0  # 默认权重

                        index[metric_id] = metric_config

        logger.info(f"Indexed {len(index)} evaluation metrics")
        return index

    def evaluate_task(
        self,
        task_result: Dict[str, Any],
        metrics_to_use: Optional[List[str]] = None
    ) -> EvaluationResult:
        """
        评估单个测试任务

        Args:
            task_result: 测试结果字典（来自TestResult.to_dict()）
            metrics_to_use: 要使用的指标ID列表，None表示使用所有适用指标

        Returns:
            评估结果
        """
        task_id = task_result.get('task_id', 'unknown')
        task_name = task_result.get('task_name', 'Unknown')

        # 1. 确定要使用的指标
        if metrics_to_use is None:
            metrics_to_use = list(self.metrics_index.keys())

        # 2. 计算各指标得分
        metric_scores = []
        for metric_id in metrics_to_use:
            if metric_id not in self.metrics_index:
                continue

            metric_def = self.metrics_index[metric_id]
            score = self._calculate_metric_score(task_result, metric_def)

            metric_scores.append(MetricScore(
                metric_id=metric_id,
                metric_name=metric_def.get('name', 'Unknown'),
                score=score,
                weight=metric_def.get('weight', 1.0),
                category=metric_def.get('category', 'general')
            ))

        # 3. 计算分类得分
        category_scores = self._calculate_category_scores(metric_scores)

        # 4. 计算总分
        overall_score = self._calculate_overall_score(metric_scores)

        # 5. 判断是否通过
        pass_threshold = 0.7  # 70%通过阈值
        pass_status = overall_score >= pass_threshold

        return EvaluationResult(
            task_id=task_id,
            task_name=task_name,
            overall_score=overall_score,
            category_scores=category_scores,
            metric_scores=metric_scores,
            pass_status=pass_status,
            timestamp=datetime.now().isoformat()
        )

    def _calculate_metric_score(
        self,
        task_result: Dict[str, Any],
        metric_def: Dict[str, Any]
    ) -> float:
        """
        计算单个指标得分

        简化实现：基于任务状态和基本信息计算得分
        """
        # 基础得分：根据任务状态
        status = task_result.get('status', 'error')
        if status == 'success':
            base_score = 0.9
        elif status == 'failed':
            base_score = 0.5
        else:  # error
            base_score = 0.3

        # 根据指标类型调整得分
        metric_category = metric_def.get('category', 'general')

        if metric_category == 'accuracy':
            # 精确度指标：成功任务得高分
            return base_score
        elif metric_category == 'efficiency':
            # 效率指标：考虑耗时
            duration = task_result.get('duration', 0)
            if duration < 1.0:
                return min(1.0, base_score + 0.1)
            return base_score
        elif metric_category == 'cost':
            # 成本指标：考虑成本
            cost = task_result.get('estimated_cost', 0)
            if cost < 0.1:
                return min(1.0, base_score + 0.1)
            return base_score
        else:
            return base_score

    def _calculate_category_scores(
        self,
        metric_scores: List[MetricScore]
    ) -> Dict[str, float]:
        """计算分类得分"""
        category_scores = {}
        category_weights = {}

        for metric in metric_scores:
            cat = metric.category
            if cat not in category_scores:
                category_scores[cat] = 0.0
                category_weights[cat] = 0.0

            category_scores[cat] += metric.weighted_score
            category_weights[cat] += metric.weight

        # 归一化
        for cat in category_scores:
            if category_weights[cat] > 0:
                category_scores[cat] /= category_weights[cat]

        return category_scores

    def _calculate_overall_score(self, metric_scores: List[MetricScore]) -> float:
        """计算总分"""
        if not metric_scores:
            return 0.0

        total_weighted = sum(m.weighted_score for m in metric_scores)
        total_weight = sum(m.weight for m in metric_scores)

        return total_weighted / total_weight if total_weight > 0 else 0.0

    def evaluate_all(
        self,
        test_results: List[Dict[str, Any]]
    ) -> List[EvaluationResult]:
        """
        批量评估测试结果

        Args:
            test_results: 测试结果列表（来自TestResult.to_dict()）

        Returns:
            评估结果列表
        """
        logger.info(f"Evaluating {len(test_results)} test results...")

        evaluation_results = []
        for result in test_results:
            eval_result = self.evaluate_task(result)
            evaluation_results.append(eval_result)

        return evaluation_results

    def generate_report(
        self,
        evaluation_results: List[EvaluationResult],
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        生成评估报告

        Args:
            evaluation_results: 评估结果列表
            output_path: 报告输出路径

        Returns:
            报告数据字典
        """
        if not evaluation_results:
            logger.warning("No evaluation results to report")
            return {}

        # 统计数据
        total = len(evaluation_results)
        passed = sum(1 for r in evaluation_results if r.pass_status)
        failed = total - passed
        avg_score = sum(r.overall_score for r in evaluation_results) / total if total > 0 else 0.0

        # 分类得分统计
        all_categories = set()
        for result in evaluation_results:
            all_categories.update(result.category_scores.keys())

        category_averages = {}
        for cat in all_categories:
            scores = [r.category_scores.get(cat, 0.0) for r in evaluation_results]
            category_averages[cat] = sum(scores) / len(scores) if scores else 0.0

        report = {
            'summary': {
                'total_tasks': total,
                'passed': passed,
                'failed': failed,
                'pass_rate': f"{(passed/total*100):.1f}%" if total > 0 else "0%",
                'average_score': f"{avg_score:.3f}",
                'category_averages': {k: f"{v:.3f}" for k, v in category_averages.items()}
            },
            'results': [r.to_dict() for r in evaluation_results],
            'timestamp': datetime.now().isoformat()
        }

        # 写入文件
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(report, f, allow_unicode=True, default_flow_style=False)

            logger.info(f"Evaluation report saved to: {output_path}")

        return report

    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取评估指标摘要"""
        categories = {}

        for metric_id, metric_def in self.metrics_index.items():
            cat = metric_def.get('category', 'general')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append({
                'id': metric_id,
                'name': metric_def.get('name'),
                'weight': metric_def.get('weight', 1.0)
            })

        return {
            'total_metrics': len(self.metrics_index),
            'categories': categories
        }


# 便捷函数
def create_evaluator(base_path: Optional[Path] = None) -> Evaluator:
    """创建评估器实例"""
    return Evaluator(base_path)


if __name__ == '__main__':
    # 测试代码
    evaluator = Evaluator()

    print("=== 测试评估系统 ===\n")

    # 测试1: 获取评估指标摘要
    print("1. 评估指标摘要:")
    summary = evaluator.get_metrics_summary()
    print(f"   Total metrics: {summary['total_metrics']}")
    print(f"   Categories: {list(summary['categories'].keys())}")

    # 测试2: 评估单个任务结果
    print("\n2. 评估单个任务结果:")
    mock_result = {
        'task_id': 'TEST-001',
        'task_name': 'Test Task',
        'status': 'success',
        'duration': 0.5,
        'selected_model': 'claude-opus-4.8',
        'estimated_cost': 0.08,
        'steps_completed': 5
    }
    eval_result = evaluator.evaluate_task(mock_result)
    print(f"   Task: {eval_result.task_name}")
    print(f"   Overall score: {eval_result.overall_score:.3f}")
    print(f"   Pass status: {eval_result.pass_status}")
    print(f"   Categories: {list(eval_result.category_scores.keys())}")

    # 测试3: 批量评估
    print("\n3. 批量评估:")
    mock_results = [mock_result] * 3
    eval_results = evaluator.evaluate_all(mock_results)
    print(f"   Evaluated {len(eval_results)} results")

    # 测试4: 生成报告
    print("\n4. 生成评估报告:")
    report = evaluator.generate_report(eval_results)
    if report:
        print(f"   Summary: {report['summary']}")

    print("\n✅ 评估系统验证完成")


