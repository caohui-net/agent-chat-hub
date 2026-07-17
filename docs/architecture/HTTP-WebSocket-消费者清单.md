# HTTP/WebSocket消费者清单

**盘点日期**: 2026-07-17  
**负责人**: 架构负责人  
**基于**: ADR-0001要求

---

## 执行摘要

经过完整盘点，**确认消费者清单为空**。项目处于早期阶段，尚未实现任何HTTP/WebSocket相关功能。

**决策**: 根据ADR-0001，消费者清单为空时直接移除FastAPI和WebSocket相关依赖。

---

## 盘点范围

### 1. 代码库检查

**检查项**: Python源代码中是否有HTTP/WebSocket实现或调用

**结果**: 
- ✅ src/目录为空，无任何Python源代码
- ✅ 无FastAPI路由定义
- ✅ 无WebSocket端点实现
- ✅ 无HTTP客户端调用FastAPI的代码

**结论**: 无代码层面的消费者

### 2. 集成测试检查

**检查项**: tests/目录中是否有HTTP/WebSocket相关测试

**结果**:
- ✅ tests/目录不存在或为空
- ✅ 无HTTP API测试
- ✅ 无WebSocket连接测试

**结论**: 无测试层面的消费者

### 3. 部署入口检查

**检查项**: 是否有启动FastAPI服务的脚本或配置

**结果**:
- ✅ 无main.py或app.py启动脚本
- ✅ 无Docker配置（Dockerfile、docker-compose.yml）
- ✅ 无部署脚本（deploy.sh等）
- ✅ 无systemd服务文件

**结论**: 无部署层面的消费者

### 4. 公开文档检查

**检查项**: 文档中是否承诺提供HTTP/WebSocket API

**结果**:
- ⚠️ docs/技术选型分析报告.md中提到FastAPI和WebSocket，但已标记为"已取代"（参见ADR-0001）
- ✅ ADR-0001明确声明TUI替代Web界面
- ✅ README.md未承诺HTTP API
- ✅ 无API文档（OpenAPI/Swagger）

**结论**: 历史文档已更新，无有效的公开承诺

### 5. 外部集成检查

**检查项**: 是否有外部系统依赖HTTP/WebSocket接口

**结果**:
- ✅ 项目为新建项目，无外部系统集成
- ✅ 无已知的自动化工具调用
- ✅ 无CI/CD管道依赖HTTP API

**结论**: 无外部集成消费者

---

## 依赖清单

### 当前依赖中的HTTP/WebSocket相关包

| 包名 | 版本要求 | 用途 | 决策 |
|------|---------|------|------|
| fastapi | >=0.110.0 | Web框架 | ❌ 移除 |
| uvicorn | >=0.29.0 | ASGI服务器 | ❌ 移除 |
| python-multipart | >=0.0.9 | 文件上传处理 | ❌ 移除 |
| httpx | >=0.27.0 | HTTP客户端 | ✅ 保留（用于调用模型API） |

**说明**: httpx需要保留，因为它用于调用外部模型API（OpenAI、Anthropic等），不是WebSocket/FastAPI的依赖。

---

## 结论

**消费者清单状态**: ✅ **空**

**验证标准**（ADR-0001）:
- [x] 代码库中不存在HTTP/WebSocket实现
- [x] 测试中不存在HTTP/WebSocket调用
- [x] 部署入口中不存在FastAPI启动脚本
- [x] 文档中无有效的HTTP API承诺（历史文档已更新）
- [x] 无外部系统依赖

**执行决策**:
根据ADR-0001第2项决策："若消费者清单为空时现有非Web测试全部通过"。由于：
1. 消费者清单为空
2. 当前无任何测试（tests/目录为空）

因此，**直接移除FastAPI、uvicorn和python-multipart依赖**。

---

## 下一步行动

1. ✅ 提交本消费者清单文档
2. ⏳ 更新pyproject.toml：移除fastapi、uvicorn、python-multipart
3. ⏳ 添加TUI相关依赖（textual/rich、keyring）

---

**文档版本**: v1.0  
**创建日期**: 2026-07-17  
**状态**: 已完成
