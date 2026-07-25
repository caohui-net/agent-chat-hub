#!/usr/bin/env python3
"""
AI角色系统 - 模型路由器

根据任务类型、成本约束和模型能力进行智能路由。
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


@dataclass
class ModelCapability:
    """模型能力描述"""
    model_id: str
    vendor: str
    tier: str
    strengths: List[str]
    weaknesses: List[str]
    input_cost: float  # USD per 1M tokens
    output_cost: float  # USD per 1M tokens
    max_context: int
    reasoning_depth: int

    @classmethod
    def from_dict(cls, model_id: str, data: Dict[str, Any]) -> 'ModelCapability':
        """从字典创建"""
        pricing = data.get('pricing', {})
        performance = data.get('performance', {})
        capabilities = data.get('capabilities', {})
        long_context = capabilities.get('long_context', {})

        return cls(
            model_id=model_id,
            vendor=data.get('vendor', 'unknown'),
            tier=data.get('tier', 'standard'),
            strengths=data.get('strengths', []),
            weaknesses=data.get('weaknesses', []),
            input_cost=pricing.get('input', 0.0),
            output_cost=pricing.get('output', 0.0),
            max_context=long_context.get('max_tokens', 0),
            reasoning_depth=performance.get('reasoning_depth', 5)
        )

    @property
    def cost_per_1k_tokens(self) -> float:
        """平均成本（输入输出1:1比例）"""
        return (self.input_cost + self.output_cost) / 2000  # per 1k tokens


@dataclass
class RoutingDecision:
    """路由决策结果"""
    selected_model: str
    reason: str
    estimated_cost: float
    fallback_models: List[str]
    confidence: float  # 0.0-1.0

    def __str__(self):
        return f"Model: {self.selected_model} (confidence: {self.confidence:.2f}, reason: {self.reason})"


class ModelRouter:
    """模型路由器核心"""

    def __init__(self, base_path: Optional[Path] = None):
        """
        初始化模型路由器

        Args:
            base_path: ai-role-system目录路径
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = Path(base_path)
        self.models_dir = self.base_path / 'model-config'

        if not self.models_dir.exists():
            raise ValueError(f"Model config directory not found: {self.models_dir}")

        # 加载配置
        self.routing_matrix = self._load_yaml('routing-matrix.yaml')
        self.capability_profiles = self._load_yaml('capability-profiles.yaml')
        self.cost_thresholds = self._load_yaml('cost-thresholds.yaml')

        # 构建模型索引
        self.models: Dict[str, ModelCapability] = {}
        self._build_model_index()

    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """加载YAML配置文件"""
        file_path = self.models_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Error loading {filename}: {e}")

    def _build_model_index(self):
        """构建模型能力索引"""
        if 'models' not in self.capability_profiles:
            return

        # capability_profiles['models'] 是字典: {model_id: config}
        for model_id, model_data in self.capability_profiles['models'].items():
            capability = ModelCapability.from_dict(model_id, model_data)
            self.models[capability.model_id] = capability

        logger.info(f"Indexed {len(self.models)} models")

    def route(
        self,
        task_type: str,
        complexity: TaskComplexity,
        context_size: Optional[int] = None,
        cost_budget: Optional[float] = None
    ) -> RoutingDecision:
        """
        执行模型路由决策

        Args:
            task_type: 任务类型 (如 'code_review', 'requirements', 'testing')
            complexity: 任务复杂度
            context_size: 预估上下文大小（tokens）
            cost_budget: 成本预算上限

        Returns:
            路由决策结果
        """
        # 1. 从路由矩阵获取推荐模型
        recommended_models = self._get_recommended_models(task_type, complexity)

        if not recommended_models:
            logger.warning(f"No recommended models for {task_type}/{complexity}")
            recommended_models = ['claude-opus-4.8']  # 默认回退

        # 2. 应用成本约束
        if cost_budget:
            recommended_models = self._filter_by_cost(recommended_models, cost_budget, context_size)

        # 3. 应用上下文大小约束
        if context_size:
            recommended_models = self._filter_by_context(recommended_models, context_size)

        # 4. 选择最佳模型
        if not recommended_models:
            logger.warning("No models match constraints, using fallback")
            selected_model = 'claude-opus-4.8'
            confidence = 0.5
            reason = "Fallback: constraints too strict"
        else:
            selected_model = recommended_models[0]
            confidence = 0.9 if len(recommended_models) >= 2 else 0.7
            reason = f"Best match for {task_type}/{complexity.value}"

        # 5. 估算成本
        estimated_cost = self._estimate_cost(selected_model, context_size or 1000)

        # 6. 构建决策
        return RoutingDecision(
            selected_model=selected_model,
            reason=reason,
            estimated_cost=estimated_cost,
            fallback_models=recommended_models[1:3] if len(recommended_models) > 1 else [],
            confidence=confidence
        )

    def _get_recommended_models(
        self,
        task_type: str,
        complexity: TaskComplexity
    ) -> List[str]:
        """从路由矩阵获取推荐模型"""
        if 'task_types' not in self.routing_matrix:
            return []

        for task in self.routing_matrix['task_types']:
            if task.get('type') == task_type:
                recommendations = task.get('recommendations', {})
                models = recommendations.get(complexity.value, [])
                return [m['model'] for m in models] if models else []

        return []

    def _filter_by_cost(
        self,
        models: List[str],
        budget: float,
        context_size: Optional[int]
    ) -> List[str]:
        """按成本预算过滤模型"""
        if not context_size:
            context_size = 1000

        filtered = []
        for model_id in models:
            if model_id not in self.models:
                continue

            estimated_cost = self._estimate_cost(model_id, context_size)
            if estimated_cost <= budget:
                filtered.append(model_id)

        return filtered

    def _filter_by_context(
        self,
        models: List[str],
        context_size: int
    ) -> List[str]:
        """按上下文大小过滤模型"""
        return [
            m for m in models
            if m in self.models and self.models[m].max_context >= context_size
        ]

    def _estimate_cost(self, model_id: str, context_size: int) -> float:
        """估算成本（美元）"""
        if model_id not in self.models:
            return 0.0

        model = self.models[model_id]
        # 假设输入输出比例1:1
        total_tokens = context_size * 2
        return (total_tokens / 1000) * model.cost_per_1k_tokens

    def get_model_info(self, model_id: str) -> Optional[ModelCapability]:
        """获取模型能力信息"""
        return self.models.get(model_id)

    def list_models(self) -> List[str]:
        """列出所有可用模型"""
        return list(self.models.keys())

    def get_cost_threshold(self, threshold_type: str) -> Optional[float]:
        """获取成本阈值配置"""
        thresholds = self.cost_thresholds.get('thresholds', [])
        for t in thresholds:
            if t.get('type') == threshold_type:
                return t.get('daily_limit')
        return None


# 便捷函数
def create_router(base_path: Optional[Path] = None) -> ModelRouter:
    """创建模型路由器实例"""
    return ModelRouter(base_path)


if __name__ == '__main__':
    # 测试代码
    router = ModelRouter()

    print("=== 测试模型路由器 ===\n")

    # 测试1: 列出所有模型
    print("1. 可用模型:")
    models = router.list_models()
    for model_id in models:
        print(f"   - {model_id}")

    # 测试2: 获取模型信息
    print("\n2. Claude Opus 4.8信息:")
    opus_info = router.get_model_info('claude-opus-4.8')
    if opus_info:
        print(f"   Vendor: {opus_info.vendor}")
        print(f"   Tier: {opus_info.tier}")
        print(f"   Input cost: ${opus_info.input_cost}/1M tokens")
        print(f"   Output cost: ${opus_info.output_cost}/1M tokens")
        print(f"   Max context: {opus_info.max_context}")
        print(f"   Reasoning depth: {opus_info.reasoning_depth}/10")

    # 测试3: 路由决策 - 简单任务
    print("\n3. 路由决策 - 简单代码审查:")
    decision = router.route('code_review', TaskComplexity.SIMPLE, context_size=2000)
    print(f"   {decision}")
    print(f"   Estimated cost: ${decision.estimated_cost:.4f}")

    # 测试4: 路由决策 - 复杂任务
    print("\n4. 路由决策 - 复杂架构设计:")
    decision = router.route('architecture', TaskComplexity.COMPLEX, context_size=5000)
    print(f"   {decision}")
    print(f"   Fallbacks: {decision.fallback_models}")

    # 测试5: 成本预算约束
    print("\n5. 路由决策 - 带成本约束:")
    decision = router.route('testing', TaskComplexity.MEDIUM, context_size=3000, cost_budget=0.05)
    print(f"   {decision}")
    print(f"   Estimated cost: ${decision.estimated_cost:.4f}")

    print("\n✅ 模型路由器测试完成")


