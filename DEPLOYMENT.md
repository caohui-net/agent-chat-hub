# 部署指南

本文档说明如何将Agent Chat Hub部署到生产环境。

## 部署前准备

### 系统要求

- **操作系统**: Linux (推荐Ubuntu 22.04+) 或 macOS
- **Python**: 3.14 或更高版本
- **内存**: 至少 2GB RAM
- **存储**: 至少 500MB 可用空间

### 环境检查

```bash
# 检查Python版本
python3 --version  # 应该 ≥ 3.14

# 检查pip
python3 -m pip --version
```

---

## 部署方式

### 方式1: 标准部署（推荐）

**1. 克隆项目**

```bash
git clone https://github.com/caohui-net/agent-chat-hub.git
cd agent-chat-hub
```

**2. 创建生产环境**

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e .
```

**3. 配置API密钥**

```bash
# 运行配置脚本
python init_config.py
```

按提示输入：
- 选择模型provider (Anthropic/OpenAI)
- 输入API密钥（安全存储到系统密钥环）
- 创建agent配置

**4. 验证安装**

```bash
# 运行测试
pytest tests/ -v

# 启动应用
python main.py
```

---

### 方式2: Docker部署

**1. 创建Dockerfile**

```dockerfile
FROM python:3.14-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app

# 安装Python依赖
RUN pip install -e .

# 暴露端口（如需要）
# EXPOSE 8000

# 启动命令
CMD ["python3", "main.py"]
```

**2. 构建镜像**

```bash
docker build -t agent-chat-hub:latest .
```

**3. 运行容器**

```bash
docker run -it \
  -v ~/.agent-chat-hub:/root/.agent-chat-hub \
  agent-chat-hub:latest
```

---

## 配置管理

### 配置文件位置

```
~/.agent-chat-hub/
├── models.json     # 模型配置
├── agents.json     # Agent配置
├── sessions/       # 会话历史
└── files/          # 文件存储
```

### API密钥管理

API密钥通过系统密钥环安全存储，不保存到文件。

**查看已存储的密钥：**
```bash
# macOS
security find-generic-password -s "agent-chat-hub"

# Linux (使用Secret Service)
secret-tool search service agent-chat-hub
```

**更新API密钥：**
```bash
python init_config.py
# 选择相同的provider，输入新密钥即可覆盖
```

---

## 运行管理

### 启动应用

**方式1: 启动脚本（推荐）**
```bash
./start.sh
```

**方式2: 手动启动**
```bash
source venv/bin/activate
python main.py
```

### 停止应用

- **正常退出**: 按 `Ctrl+C` 或 `Ctrl+Q`
- **强制退出**: 按 `Ctrl+C` 两次

### 后台运行

使用`tmux`或`screen`：

```bash
# 使用tmux
tmux new -s agent-chat
python main.py

# 退出会话（不停止应用）: Ctrl+B, D
# 重新连接: tmux attach -t agent-chat
```

---

## 数据备份

### 备份配置

```bash
# 备份配置目录
tar -czf agent-chat-backup-$(date +%Y%m%d).tar.gz ~/.agent-chat-hub/
```

### 恢复配置

```bash
# 恢复备份
tar -xzf agent-chat-backup-20260726.tar.gz -C ~/
```

---

## 更新升级

### 更新到最新版本

```bash
cd agent-chat-hub

# 拉取最新代码
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -e . --upgrade

# 重启应用
python main.py
```

---

## 安全建议

1. **API密钥保护**
   - 使用系统密钥环存储
   - 不要将密钥提交到Git
   - 定期轮换API密钥

2. **权限控制**
   - 配置目录权限：`chmod 700 ~/.agent-chat-hub/`
   - 会话文件权限：`chmod 600 ~/.agent-chat-hub/sessions/*`

3. **网络安全**
   - 仅在可信网络使用
   - 如需远程访问，使用SSH隧道

---

## 故障排查

### 常见问题

**问题1: 找不到配置文件**
```
错误: Config file not found at ~/.agent-chat-hub/models.json
解决: python init_config.py
```

**问题2: API密钥无效**
```
错误: Invalid API key
解决: 
1. 检查密钥是否正确
2. python init_config.py 重新配置
3. 验证provider选择正确（Anthropic vs OpenAI）
```

**问题3: 依赖安装失败**
```
错误: externally-managed-environment
解决: 使用虚拟环境
  python3 -m venv venv
  source venv/bin/activate
  pip install -e .
```

**问题4: 端口占用（未来WebSocket版本）**
```
错误: Address already in use
解决: 
  lsof -i :8000
  kill <PID>
```

---

## 性能优化

### 资源限制

当前MVP预算限制：
- 最大并发agents: 3
- 每轮最大调用次数: 3
- 最大token数: 12,000
- 超时时间: 120秒

可在配置中调整（未来版本）。

### 监控建议

- 使用`htop`监控CPU/内存
- 检查`~/.agent-chat-hub/sessions/`大小
- 定期清理旧会话文件

---

## 支持

- **问题反馈**: GitHub Issues
- **文档**: `/docs` 目录
- **测试**: `pytest tests/ -v`

---

**更新时间**: 2026-07-26
**版本**: 0.1.0
