#!/usr/bin/env python3
"""
AI角色系统 - 基础使用示例

展示如何加载角色配置、规则和模型路由。
这是最简单的集成示例，适合快速上手。
"""

import yaml
from pathlib import Path
import json


class AIRoleSystem:
    """AI角色系统加载器"""

    def __init__(self, base_path=None):
        """
        初始化系统

        Args:
            base_path: ai-role-system目录路径，默认为脚本所在目录的上级
        """
        if base_path is None:
            # 默认路径：examples/../
            base_path = Path(__file__).parent.parent

        self.base_path = Path(base_path)
        self.roles = {}
        self.rules = {}
        self.routing = None
        self.models = None

        self._load_all_config()

    def _load_all_config(self):
        """加载所有配置文件"""
        print(f"📂 正在从 {self.base_path} 加载配置...\n")

        # 加载角色
        self._load_roles()

        # 加载规则
        self._load_rules()

        # 加载模型配置
        self._load_model_config()

        print("✅ 配置加载完成\n")

    def _load_roles(self):
        """加载所有角色配置"""
        roles_dir = self.base_path / 'roles'
        for role_file in roles_dir.glob('*.yaml'):
            with open(role_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                role_id = role_file.stem
                self.roles[role_id] = config

        print(f"  ✓ 加载了 {len(self.roles)} 个角色")

    def _load_rules(self):
        """加载所有规则"""
        rules_dir = self.base_path / 'rules'
        for rule_file in rules_dir.glob('*.yaml'):
            if rule_file.name == 'README.md':
                continue
            with open(rule_file, 'r', encoding='utf-8') as f:
                rules_list = yaml.safe_load(f)
                if isinstance(rules_list, list):
                    for rule in rules_list:
                        self.rules[rule['id']] = rule

        print(f"  ✓ 加载了 {len(self.rules)} 条规则")

    def _load_model_config(self):
        """加载模型配置"""
        model_config_dir = self.base_path / 'model-config'

        # 加载路由矩阵
        with open(model_config_dir / 'routing-matrix.yaml', 'r', encoding='utf-8') as f:
            self.routing = yaml.safe_load(f)

        # 加载能力配置
        with open(model_config_dir / 'capability-profiles.yaml', 'r', encoding='utf-8') as f:
            self.models = yaml.safe_load(f)

        print(f"  ✓ 加载了模型路由配置")

    def get_role(self, role_id):
        """
        获取角色配置

        Args:
            role_id: 角色ID（analyst/architect/developer/reviewer/qa/devops）

        Returns:
            角色配置字典，如果不存在返回None
        """
        return self.roles.get(role_id)

    def get_role_info(self, role_id):
        """
        获取角色基本信息

        Args:
            role_id: 角色ID

        Returns:
            包含name和mission的字典
        """
        role = self.get_role(role_id)
        if not role:
            return None

        return {
            'id': role_id,
            'name': role['role']['name'],
            'mission': role['role']['mission']
        }

    def get_recommended_model(self, role_id):
        """
        获取角色推荐的主模型

        Args:
            role_id: 角色ID

        Returns:
            模型ID字符串，如 'claude-sonnet-5'
        """
        routing = self.routing['routing_matrix'].get(role_id)
        if routing:
            return routing['primary']['model']
        return None

    def get_model_info(self, model_id):
        """
        获取模型详细信息

        Args:
            model_id: 模型ID

        Returns:
            模型配置字典
        """
        models = self.models.get('models', {})
        return models.get(model_id)

    def get_rules_for_role(self, role_id):
        """
        获取角色应用的规则列表

        Args:
            role_id: 角色ID

        Returns:
            规则对象列表
        """
        role = self.get_role(role_id)
        if not role or 'constraints' not in role:
            return []

        rule_refs = role['constraints'].get('rules', [])
        rule_ids = [r['id'] for r in rule_refs]

        return [self.rules[rid] for rid in rule_ids if rid in self.rules]

    def list_roles(self):
        """列出所有可用角色"""
        return list(self.roles.keys())

    def list_rules(self):
        """列出所有可用规则"""
        return list(self.rules.keys())


def demo_basic_usage():
    """演示基本使用"""
    print("=" * 60)
    print("AI角色系统 - 基础使用示例")
    print("=" * 60)
    print()

    # 初始化系统
    system = AIRoleSystem()

    # 1. 列出所有角色
    print("📋 可用角色:")
    for role_id in system.list_roles():
        info = system.get_role_info(role_id)
        print(f"  • {info['name']} ({role_id})")
        print(f"    职责: {info['mission'][:50]}...")
    print()

    # 2. 查看特定角色详情
    print("🔍 角色详情示例: Code Reviewer")
    print("-" * 60)

    reviewer = system.get_role('reviewer')
    print(f"名称: {reviewer['role']['name']}")
    print(f"职责: {reviewer['role']['mission']}")
    print(f"输出格式: {reviewer['output_contract']['format']}")
    print(f"输出字段: {', '.join(reviewer['output_contract']['schema']['properties'].keys())}")
    print()

    # 3. 获取推荐模型
    model_id = system.get_recommended_model('reviewer')
    model_info = system.get_model_info(model_id)
    print(f"推荐模型: {model_id}")
    print(f"  定价: ${model_info['pricing']['input']}/M输入, ${model_info['pricing']['output']}/M输出")
    print(f"  推理深度: {model_info['performance']['reasoning_depth']}/10")
    print()

    # 4. 查看应用的规则
    rules = system.get_rules_for_role('reviewer')
    print(f"应用规则数量: {len(rules)}")
    for rule in rules[:3]:
        print(f"  • {rule['id']}: {rule['name']} [{rule['severity']}]")
    print()

    # 5. 列出所有规则
    print(f"📝 规则库包含 {len(system.list_rules())} 条规则:")
    for rule_id in sorted(system.list_rules())[:5]:
        rule = system.rules[rule_id]
        print(f"  • {rule_id}: {rule['name']}")
    print(f"  ... 还有 {len(system.list_rules()) - 5} 条规则")
    print()

    print("=" * 60)
    print("✅ 示例完成")
    print("=" * 60)


def demo_role_comparison():
    """演示角色对比"""
    print("\n" + "=" * 60)
    print("角色对比示例")
    print("=" * 60)
    print()

    system = AIRoleSystem()

    # 对比developer和reviewer
    roles_to_compare = ['developer', 'reviewer']

    print(f"对比角色: {', '.join(roles_to_compare)}")
    print("-" * 60)

    for role_id in roles_to_compare:
        info = system.get_role_info(role_id)
        model_id = system.get_recommended_model(role_id)
        model_info = system.get_model_info(model_id)
        rules = system.get_rules_for_role(role_id)

        print(f"\n{info['name']} ({role_id}):")
        print(f"  推荐模型: {model_id}")
        print(f"  模型成本: ${model_info['pricing']['input']}/M输入")
        print(f"  应用规则: {len(rules)}条")
        print(f"  规则列表: {', '.join([r['id'] for r in rules[:3]])}")


if __name__ == '__main__':
    # 运行基础示例
    demo_basic_usage()

    # 运行对比示例
    demo_role_comparison()
