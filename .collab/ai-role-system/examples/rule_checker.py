#!/usr/bin/env python3
"""
规则检查器 - 自动化应用原子规则检查代码

这个脚本演示如何自动检查代码是否违反安全规则。
支持检查的规则包括：SEC-001, SEC-002, SEC-003, SEC-004
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any


class RuleChecker:
    """规则检查器"""

    def __init__(self, base_path=None):
        """初始化规则检查器"""
        if base_path is None:
            base_path = Path(__file__).parent.parent

        self.base_path = Path(base_path)
        self.rules = {}
        self._load_rules()

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

    def check_code(self, code: str, rule_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        检查代码是否违反规则

        Args:
            code: 要检查的代码内容
            rule_ids: 要检查的规则ID列表，None表示检查所有规则

        Returns:
            违规列表，每项包含 rule_id, severity, message
        """
        if rule_ids is None:
            rule_ids = list(self.rules.keys())

        violations = []

        for rule_id in rule_ids:
            if rule_id not in self.rules:
                continue

            rule = self.rules[rule_id]

            # 根据规则ID调用相应的检查方法
            if rule_id == 'SEC-001':
                result = self._check_sec_001(code, rule)
            elif rule_id == 'SEC-002':
                result = self._check_sec_002(code, rule)
            elif rule_id == 'SEC-003':
                result = self._check_sec_003(code, rule)
            elif rule_id == 'SEC-004':
                result = self._check_sec_004(code, rule)
            else:
                continue  # 不支持的规则

            if result:
                violations.append({
                    'rule_id': rule_id,
                    'rule_name': rule['name'],
                    'severity': rule['severity'],
                    'message': result
                })

        return violations

    def _check_sec_001(self, code: str, rule: Dict) -> str:
        """
        检查 SEC-001: 所有对象访问必须验证权限

        检测模式：
        - 查询数据库但缺少用户ID过滤
        """
        # 简化检测：查找SELECT语句但不包含user_id或tenant_id
        if 'SELECT' in code or 'select' in code:
            # 检查是否有用户过滤
            if not re.search(r'(user_id|tenant_id|current_user)', code, re.IGNORECASE):
                return "查询语句可能缺少权限验证（未找到user_id/tenant_id过滤）"
        return None

    def _check_sec_002(self, code: str, rule: Dict) -> str:
        """
        检查 SEC-002: 敏感数据不得记录到日志

        检测模式：
        - 日志语句包含password/token/secret等敏感字段
        """
        # 检查日志语句
        log_patterns = [
            r'logger\.(info|debug|error|warn).*password',
            r'console\.log.*password',
            r'print.*password',
            r'logger\.(info|debug|error|warn).*token',
            r'console\.log.*token',
        ]

        for pattern in log_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return "日志语句可能包含敏感信息（password/token）"

        return None

    def _check_sec_003(self, code: str, rule: Dict) -> str:
        """
        检查 SEC-003: 用户输入必须验证和清理

        检测模式：
        - SQL拼接（SQL注入风险）
        - 缺少输入验证
        """
        # 检查SQL拼接
        sql_injection_patterns = [
            r'SELECT.*\$\{',  # JavaScript模板字符串拼接
            r'SELECT.*\+.*\+',  # 字符串拼接
            r'query\([\'"`]SELECT.*[\'"`]\s*\+',  # 直接拼接
        ]

        for pattern in sql_injection_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return "发现SQL拼接，可能存在SQL注入风险（应使用参数化查询）"

        return None

    def _check_sec_004(self, code: str, rule: Dict) -> str:
        """
        检查 SEC-004: 密码和密钥不得硬编码

        检测模式：
        - 硬编码的密码/API密钥/JWT密钥
        """
        # 检查硬编码密钥
        hardcoded_patterns = [
            r'password\s*=\s*[\'"][^\'"]{8,}[\'"]',
            r'apiKey\s*=\s*[\'"][^\'"]{10,}[\'"]',
            r'secret\s*=\s*[\'"][^\'"]{10,}[\'"]',
            r'jwt\.sign\([^,]+,\s*[\'"][^\'"]{10,}[\'"]',
        ]

        for pattern in hardcoded_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return "发现硬编码的密钥或密码（应使用环境变量）"

        return None

    def check_file(self, file_path: str, rule_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        检查文件是否违反规则

        Args:
            file_path: 文件路径
            rule_ids: 要检查的规则ID列表

        Returns:
            违规列表
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        violations = self.check_code(code, rule_ids)

        # 添加文件路径信息
        for v in violations:
            v['file'] = file_path

        return violations


def demo_check_code():
    """演示代码检查"""
    print("=" * 60)
    print("规则检查器 - 代码检查示例")
    print("=" * 60)
    print()

    checker = RuleChecker()

    # 测试用例1: 违反SEC-001（缺少权限验证）
    print("【测试1】SEC-001: 权限验证检查")
    print("-" * 60)
    bad_code_1 = """
    async function getDocument(documentId) {
        const doc = await db.query('SELECT * FROM documents WHERE id = ?', [documentId]);
        return doc;
    }
    """
    print("代码:")
    print(bad_code_1)

    violations = checker.check_code(bad_code_1, ['SEC-001'])
    if violations:
        for v in violations:
            print(f"❌ {v['rule_id']}: {v['message']}")
    else:
        print("✅ 通过检查")
    print()

    # 测试用例2: 违反SEC-002（日志包含敏感信息）
    print("【测试2】SEC-002: 敏感信息日志检查")
    print("-" * 60)
    bad_code_2 = """
    logger.error('Login failed', {
        username: req.body.username,
        password: req.body.password
    });
    """
    print("代码:")
    print(bad_code_2)

    violations = checker.check_code(bad_code_2, ['SEC-002'])
    if violations:
        for v in violations:
            print(f"❌ {v['rule_id']}: {v['message']}")
    else:
        print("✅ 通过检查")
    print()

    # 测试用例3: 违反SEC-003（SQL注入）
    print("【测试3】SEC-003: SQL注入检查")
    print("-" * 60)
    bad_code_3 = """
    const query = `SELECT * FROM users WHERE email='${email}'`;
    await db.query(query);
    """
    print("代码:")
    print(bad_code_3)

    violations = checker.check_code(bad_code_3, ['SEC-003'])
    if violations:
        for v in violations:
            print(f"❌ {v['rule_id']}: {v['message']}")
    else:
        print("✅ 通过检查")
    print()

    # 测试用例4: 违反SEC-004（硬编码密钥）
    print("【测试4】SEC-004: 硬编码密钥检查")
    print("-" * 60)
    bad_code_4 = """
    const dbConfig = {
        host: 'db.example.com',
        user: 'admin',
        password: 'MySecretPassword123'
    };
    """
    print("代码:")
    print(bad_code_4)

    violations = checker.check_code(bad_code_4, ['SEC-004'])
    if violations:
        for v in violations:
            print(f"❌ {v['rule_id']}: {v['message']}")
    else:
        print("✅ 通过检查")
    print()

    # 测试用例5: 正确的代码（通过所有检查）
    print("【测试5】正确的代码（应通过所有检查）")
    print("-" * 60)
    good_code = """
    async function getDocument(documentId, userId) {
        // SEC-001: 包含用户ID过滤
        const doc = await db.query(
            'SELECT * FROM documents WHERE id = ? AND user_id = ?',
            [documentId, userId]
        );

        // SEC-002: 日志不包含敏感信息
        logger.info('Document accessed', { documentId, userId });

        // SEC-004: 从环境变量读取密钥
        const jwtToken = jwt.sign({ userId }, process.env.JWT_SECRET);

        return doc;
    }
    """
    print("代码:")
    print(good_code)

    violations = checker.check_code(good_code, ['SEC-001', 'SEC-002', 'SEC-003', 'SEC-004'])
    if violations:
        for v in violations:
            print(f"❌ {v['rule_id']}: {v['message']}")
    else:
        print("✅ 通过所有检查")
    print()

    print("=" * 60)
    print("✅ 检查示例完成")
    print("=" * 60)


def demo_batch_check():
    """演示批量检查"""
    print("\n" + "=" * 60)
    print("批量检查示例")
    print("=" * 60)
    print()

    checker = RuleChecker()

    # 模拟多个代码片段
    code_samples = {
        'auth.js': """
        const user = await db.query(`SELECT * FROM users WHERE email='${email}'`);
        """,
        'api.js': """
        logger.error('Auth failed', { password: req.body.password });
        """,
        'config.js': """
        const apiKey = 'sk-1234567890abcdef';
        """
    }

    print(f"检查 {len(code_samples)} 个文件:")
    print("-" * 60)

    all_violations = []
    for filename, code in code_samples.items():
        violations = checker.check_code(code)
        if violations:
            print(f"\n{filename}:")
            for v in violations:
                print(f"  ❌ {v['rule_id']}: {v['message']}")
                all_violations.append({**v, 'file': filename})
        else:
            print(f"\n{filename}: ✅ 无问题")

    print()
    print("-" * 60)
    print(f"总计发现 {len(all_violations)} 个违规")


if __name__ == '__main__':
    # 运行代码检查示例
    demo_check_code()

    # 运行批量检查示例
    demo_batch_check()
