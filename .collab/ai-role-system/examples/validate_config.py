#!/usr/bin/env python3
"""
YAML配置验证器

验证角色配置和规则定义是否符合JSON Schema规范。
帮助在修改配置后快速验证格式正确性。
"""

import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple


try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    print("⚠️  警告: jsonschema库未安装，将跳过Schema验证")
    print("   安装方法: pip install jsonschema")


class ConfigValidator:
    """配置验证器"""

    def __init__(self, base_path=None):
        """初始化验证器"""
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = Path(base_path)
        self.schemas = {}
        self._load_schemas()

    def _load_schemas(self):
        """加载所有JSON Schema"""
        schemas_dir = self.base_path / 'schemas'
        if not schemas_dir.exists():
            print(f"⚠️  Schema目录不存在: {schemas_dir}")
            return

        for schema_file in schemas_dir.glob('*.json'):
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_name = schema_file.stem
                self.schemas[schema_name] = json.load(f)

    def validate_yaml_syntax(self, file_path: Path) -> Tuple[bool, str]:
        """
        验证YAML文件语法

        Returns:
            (是否有效, 错误消息)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            return True, None
        except yaml.YAMLError as e:
            return False, str(e)
        except Exception as e:
            return False, f"读取文件失败: {str(e)}"

    def validate_role_config(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        验证角色配置文件

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        # 1. 验证YAML语法
        valid, error = self.validate_yaml_syntax(file_path)
        if not valid:
            errors.append(f"YAML语法错误: {error}")
            return False, errors

        # 2. 加载配置
        with open(file_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # 3. 验证必需字段
        required_fields = ['role', 'scope', 'inputs', 'workflow', 'output_contract']
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")

        # 4. 验证role字段
        if 'role' in config:
            role = config['role']
            role_required = ['id', 'name', 'version', 'mission']
            for field in role_required:
                if field not in role:
                    errors.append(f"role.{field} 字段缺失")

        # 5. 验证output_contract
        if 'output_contract' in config:
            contract = config['output_contract']
            if 'format' not in contract:
                errors.append("output_contract.format 字段缺失")
            if 'schema' not in contract:
                errors.append("output_contract.schema 字段缺失")

        # 6. JSON Schema验证（如果可用）
        if JSONSCHEMA_AVAILABLE and 'role-schema' in self.schemas:
            try:
                jsonschema.validate(config, self.schemas['role-schema'])
            except jsonschema.ValidationError as e:
                errors.append(f"Schema验证失败: {e.message}")

        return len(errors) == 0, errors

    def validate_rule_file(self, file_path: Path) -> Tuple[bool, List[str]]:
        """
        验证规则文件

        Returns:
            (是否有效, 错误消息列表)
        """
        errors = []

        # 1. 验证YAML语法
        valid, error = self.validate_yaml_syntax(file_path)
        if not valid:
            errors.append(f"YAML语法错误: {error}")
            return False, errors

        # 2. 加载规则
        with open(file_path, 'r', encoding='utf-8') as f:
            rules = yaml.safe_load(f)

        if not isinstance(rules, list):
            errors.append("规则文件必须是数组格式")
            return False, errors

        # 3. 验证每条规则
        for i, rule in enumerate(rules):
            rule_errors = self._validate_single_rule(rule, i)
            errors.extend(rule_errors)

        return len(errors) == 0, errors

    def _validate_single_rule(self, rule: Dict, index: int) -> List[str]:
        """验证单条规则"""
        errors = []
        prefix = f"规则[{index}]"

        # 必需字段
        required_fields = ['id', 'name', 'scope', 'condition', 'requirement',
                          'severity', 'verification', 'examples']
        for field in required_fields:
            if field not in rule:
                errors.append(f"{prefix} 缺少必需字段: {field}")

        # 验证ID格式
        if 'id' in rule:
            import re
            if not re.match(r'^[A-Z]+-\d{3}$', rule['id']):
                errors.append(f"{prefix} ID格式错误: {rule['id']} (应为 CATEGORY-NNN)")

        # 验证severity
        if 'severity' in rule:
            valid_severities = ['blocking', 'warning', 'info']
            if rule['severity'] not in valid_severities:
                errors.append(f"{prefix} severity无效: {rule['severity']}")

        # 验证examples
        if 'examples' in rule:
            examples = rule['examples']
            if 'pass' not in examples:
                errors.append(f"{prefix} 缺少pass示例")
            if 'fail' not in examples:
                errors.append(f"{prefix} 缺少fail示例")

        # JSON Schema验证（如果可用）
        if JSONSCHEMA_AVAILABLE and 'rule-schema' in self.schemas:
            try:
                # 使用schema的items部分验证单个规则对象
                rule_item_schema = self.schemas['rule-schema'].get('items', {})
                if rule_item_schema:
                    jsonschema.validate(rule, rule_item_schema)
            except jsonschema.ValidationError as e:
                errors.append(f"{prefix} Schema验证失败: {e.message}")

        return errors

    def validate_all_roles(self) -> Dict[str, Any]:
        """验证所有角色配置"""
        roles_dir = self.base_path / 'roles'
        results = {}

        for role_file in roles_dir.glob('*.yaml'):
            valid, errors = self.validate_role_config(role_file)
            results[role_file.name] = {
                'valid': valid,
                'errors': errors
            }

        return results

    def validate_all_rules(self) -> Dict[str, Any]:
        """验证所有规则文件"""
        rules_dir = self.base_path / 'rules'
        results = {}

        for rule_file in rules_dir.glob('*.yaml'):
            if rule_file.name == 'README.md':
                continue
            valid, errors = self.validate_rule_file(rule_file)
            results[rule_file.name] = {
                'valid': valid,
                'errors': errors
            }

        return results


def print_validation_results(results: Dict[str, Any], title: str):
    """打印验证结果"""
    print(f"\n{title}")
    print("=" * 60)

    total = len(results)
    valid_count = sum(1 for r in results.values() if r['valid'])

    for filename, result in sorted(results.items()):
        if result['valid']:
            print(f"✅ {filename}")
        else:
            print(f"❌ {filename}")
            for error in result['errors']:
                print(f"   • {error}")

    print("-" * 60)
    print(f"总计: {valid_count}/{total} 个文件通过验证")


def main():
    """主函数"""
    print("=" * 60)
    print("YAML配置验证器")
    print("=" * 60)

    if not JSONSCHEMA_AVAILABLE:
        print("\n⚠️  提示: 安装jsonschema库以启用完整Schema验证")
        print("   pip install jsonschema\n")

    validator = ConfigValidator()

    # 验证角色配置
    print("\n正在验证角色配置...")
    role_results = validator.validate_all_roles()
    print_validation_results(role_results, "角色配置验证结果")

    # 验证规则文件
    print("\n正在验证规则文件...")
    rule_results = validator.validate_all_rules()
    print_validation_results(rule_results, "规则文件验证结果")

    # 总结
    print("\n" + "=" * 60)
    all_valid = all(r['valid'] for r in role_results.values()) and \
                all(r['valid'] for r in rule_results.values())

    if all_valid:
        print("✅ 所有配置文件验证通过")
    else:
        print("❌ 发现配置错误，请修复后重新验证")
    print("=" * 60)


if __name__ == '__main__':
    main()
