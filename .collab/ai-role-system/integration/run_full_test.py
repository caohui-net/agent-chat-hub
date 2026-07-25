#!/usr/bin/env python3
"""
AI角色系统 - 端到端测试脚本

执行完整的测试套件并生成验证报告。
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from test_runner import TestRunner
from evaluator import Evaluator


def main():
    """执行端到端测试"""
    print("=" * 80)
    print("AI角色系统 - Phase 2 端到端验证")
    print("=" * 80)
    print()

    # 初始化
    print("1. 初始化测试组件...")
    runner = TestRunner()
    evaluator = Evaluator()
    print(f"   ✓ 加载了 {len(runner.get_tasks())} 个测试任务")
    print(f"   ✓ 加载了 {evaluator.get_metrics_summary()['total_metrics']} 个评估指标")
    print()

    # 执行测试
    print("2. 执行测试套件...")
    start_time = datetime.now()
    results = runner.run_all_tasks()
    duration = (datetime.now() - start_time).total_seconds()
    print(f"   ✓ 完成 {len(results)} 个测试任务")
    print(f"   ✓ 总耗时: {duration:.2f}秒")
    print()

    # 生成测试报告
    print("3. 生成测试报告...")
    test_report_path = Path('../reports/test_reports/phase2_test_report.yaml')
    test_report = runner.generate_report(test_report_path)
    print(f"   ✓ 测试报告: {test_report_path}")
    print(f"   ✓ 成功率: {test_report['summary']['success_rate']}")
    print(f"   ✓ 总成本: {test_report['summary']['total_cost']}")
    print()

    # 评估结果
    print("4. 评估测试结果...")
    test_results = [r.to_dict() for r in runner.results]
    eval_results = evaluator.evaluate_all(test_results)
    print(f"   ✓ 评估了 {len(eval_results)} 个测试结果")
    print()

    # 生成评估报告
    print("5. 生成评估报告...")
    eval_report_path = Path('../reports/evaluation_reports/phase2_eval_report.yaml')
    eval_report = evaluator.generate_report(eval_results, eval_report_path)
    print(f"   ✓ 评估报告: {eval_report_path}")
    print(f"   ✓ 通过率: {eval_report['summary']['pass_rate']}")
    print(f"   ✓ 平均分: {eval_report['summary']['average_score']}")
    print()

    # 总结
    print("=" * 80)
    print("验证完成")
    print("=" * 80)
    print()
    print("测试摘要:")
    for key, value in test_report['summary'].items():
        print(f"  {key}: {value}")
    print()
    print("评估摘要:")
    for key, value in eval_report['summary'].items():
        print(f"  {key}: {value}")
    print()

    return 0


if __name__ == '__main__':
    sys.exit(main())
