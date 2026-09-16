# Agent Chat Hub - 部署指南

**版本**: v1.0  
**最后更新**: 2026-09-06

---

## 目录

1. [快速部署](#快速部署)
2. [详细部署步骤](#详细部署步骤)
3. [Docker部署](#docker部署)
4. [systemd服务](#systemd服务)
5. [配置说明](#配置说明)
6. [故障排查](#故障排查)
7. [性能优化](#性能优化)

---

## 快速部署

### 前置要求

- Ubuntu 26.04 LTS 或更高版本
- Python 3.14+
- 2GB+ RAM
- 10GB+ 磁盘空间

### 一键部署

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/agent-chat-hub.git
cd agent-chat-hub

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置API密钥
cp config/config.example.json config/config.json
# 编辑 config/config.json，填入API密钥

# 5. 初始化日志目录
mkdir -p logs

# 6. 运行测试验证
pytest tests/unit/ -v

# 7. 启动应用
python3 main.py
```

**预计时间**: 5-10分钟

---

## 详细部署步骤

### 步骤1: 环境准备

#### 1.1 系统更新

```bash
sudo apt update
sudo apt upgrade -y
```

#### 1.2 安装Python 3.14+

```bash
# 检查Python版本
python3 --version

# 如果版本低于3.14，安装最新版本
sudo apt install python3.14 python3.14-venv python3.14-dev
```

#### 1.3 安装系统依赖

```bash
sudo apt install -y \
    build-essential \
    git \
    curl \
    libssl-dev \
    libffi-dev
```

---

### 步骤2: 获取代码

```bash
# 克隆仓库
git clone https://github.com/your-org/agent-chat-hub.git
cd agent-chat-hub

# 检查版本
git describe --tags

# 切换到稳定版本（推荐生产环境）
git checkout v1.0.0
```

---

### 步骤3: 配置虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 验证安装
pip check
```

---

### 步骤4: 配置应用

#### 4.1 创建配置文件

```bash
# 复制配置模板
cp config/config.example.json config/config.json

# 编辑配置文件
nano config/config.json
```

#### 4.2 配置示例

```json
{
  "models": {
    "claude-sonnet": {
      "provider": "anthropic",
      "model_id": "claude-sonnet-4-20250514",
      "base_url": "https://api.anthropic.com",
      "api_key_name": "ANTHROPIC_API_KEY",
      "max_tokens": 4096,
      "temperature": 0.7
    },
    "gpt-4": {
      "provider": "openai",
      "model_id": "gpt-4",
      "base_url": "https://api.openai.com",
      "api_key_name": "OPENAI_API_KEY",
      "max_tokens": 4096,
      "temperature": 0.7
    }
  },
  "agents": [],
  "log_level": "INFO",
  "max_concurrent_agents": 5
}
```

#### 4.3 配置API密钥

**方法1: 使用keyring（推荐）**

```bash
# 安装keyring
pip install keyring

# 设置API密钥
python3 -c "import keyring; keyring.set_password('agent-chat-hub', 'ANTHROPIC_API_KEY', 'sk-ant-...')"
python3 -c "import keyring; keyring.set_password('agent-chat-hub', 'OPENAI_API_KEY', 'sk-...')"
```

**方法2: 使用环境变量**

```bash
# 编辑 ~/.bashrc 或 ~/.profile
nano ~/.bashrc

# 添加以下内容
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="..."

# 重新加载
source ~/.bashrc
```

#### 4.4 配置Agent

```bash
# 创建Agent配置目录
mkdir -p config/agents

# 创建示例Agent
cat > config/agents/researcher.json <<EOF
{
  "agent_id": "researcher",
  "name": "研究员",
  "model_id": "claude-sonnet",
  "system_prompt": "你是一个专业的研究员，擅长信息收集和分析。",
  "active": true
}
EOF
```

---

### 步骤5: 初始化环境

```bash
# 创建日志目录
mkdir -p logs

# 创建session目录
mkdir -p ~/.agent-chat-hub/sessions

# 设置日志权限
chmod 755 logs

# 验证目录结构
tree -L 2 -d
```

---

### 步骤6: 测试验证

#### 6.1 运行单元测试

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行所有单元测试
pytest tests/unit/ -v

# 运行覆盖率测试
pytest tests/unit/ --cov=src --cov-report=html

# 查看覆盖率报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

#### 6.2 运行集成测试

```bash
pytest tests/integration/ -v
```

#### 6.3 测试API连接

```bash
# 创建测试脚本
cat > test_api.py <<EOF
import asyncio
from src.agents.executor import AgentExecutor
from src.core.config import ConfigManager

async def test():
    config_mgr = ConfigManager()
    executor = AgentExecutor(config_mgr, message_bus=None)
    
    # 测试CLI是否可用
    if executor.cli_adapter.is_available("anthropic"):
        print("✓ Claude CLI 可用")
    else:
        print("✗ Claude CLI 不可用，将使用HTTP API")
    
    print("✓ API配置测试通过")

asyncio.run(test())
EOF

# 运行测试
python3 test_api.py
```

---

### 步骤7: 启动应用

#### 7.1 前台启动（测试用）

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动应用
python3 main.py
```

#### 7.2 后台启动

```bash
# 使用nohup后台运行
nohup python3 main.py > logs/app.log 2>&1 &

# 记录PID
echo $! > /tmp/agent-chat-hub.pid

# 查看日志
tail -f logs/app.log
```

#### 7.3 停止应用

```bash
# 使用PID停止
kill $(cat /tmp/agent-chat-hub.pid)

# 或查找进程停止
pkill -f "python3 main.py"
```

---

## Docker部署

### Dockerfile

```dockerfile
FROM python:3.14-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口（如需要）
# EXPOSE 8000

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python3", "main.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  agent-chat-hub:
    build: .
    container_name: agent-chat-hub
    restart: unless-stopped
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ~/.agent-chat-hub:/root/.agent-chat-hub
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    env_file:
      - .env
    # ports:
    #   - "8000:8000"
```

### 部署步骤

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动容器
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止容器
docker-compose down

# 5. 重启容器
docker-compose restart
```

---

## systemd服务

### 服务配置文件

创建 `/etc/systemd/system/agent-chat-hub.service`:

```ini
[Unit]
Description=Agent Chat Hub
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/agent-chat-hub
Environment="PATH=/home/your-username/agent-chat-hub/venv/bin"
EnvironmentFile=/home/your-username/agent-chat-hub/.env
ExecStart=/home/your-username/agent-chat-hub/venv/bin/python3 main.py
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/your-username/agent-chat-hub/logs/service.log
StandardError=append:/home/your-username/agent-chat-hub/logs/service-error.log

[Install]
WantedBy=multi-user.target
```

### 服务管理

```bash
# 1. 创建.env文件
cat > .env <<EOF
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
EOF

# 2. 重载systemd配置
sudo systemctl daemon-reload

# 3. 启动服务
sudo systemctl start agent-chat-hub

# 4. 设置开机自启
sudo systemctl enable agent-chat-hub

# 5. 查看状态
sudo systemctl status agent-chat-hub

# 6. 查看日志
sudo journalctl -u agent-chat-hub -f

# 7. 重启服务
sudo systemctl restart agent-chat-hub

# 8. 停止服务
sudo systemctl stop agent-chat-hub
```

---

## 配置说明

### 环境变量

| 变量名 | 说明 | 必需 | 默认值 |
|--------|------|------|--------|
| `ANTHROPIC_API_KEY` | Anthropic API密钥 | 否* | - |
| `OPENAI_API_KEY` | OpenAI API密钥 | 否* | - |
| `GEMINI_API_KEY` | Google Gemini API密钥 | 否* | - |
| `LOG_LEVEL` | 日志级别 | 否 | INFO |
| `MAX_CONCURRENT_AGENTS` | 最大并发Agent数 | 否 | 5 |

*至少需要配置一个API密钥

### 日志配置

编辑 `config/logging.json`:

```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "default": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
  },
  "handlers": {
    "console": {
      "class": "logging.StreamHandler",
      "formatter": "default",
      "level": "INFO"
    },
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "filename": "logs/agent-chat-hub.log",
      "maxBytes": 10485760,
      "backupCount": 5,
      "formatter": "default",
      "level": "INFO"
    },
    "error_file": {
      "class": "logging.handlers.RotatingFileHandler",
      "filename": "logs/error.log",
      "maxBytes": 10485760,
      "backupCount": 5,
      "formatter": "default",
      "level": "ERROR"
    }
  },
  "root": {
    "level": "INFO",
    "handlers": ["console", "file", "error_file"]
  }
}
```

---

## 故障排查

### 常见问题

#### 1. 应用无法启动

**症状**: `python3 main.py` 立即退出

**排查**:
```bash
# 检查Python版本
python3 --version  # 应该 >= 3.14

# 检查依赖
pip check

# 查看详细错误
python3 main.py --debug
```

**解决**:
```bash
# 重新安装依赖
pip install --force-reinstall -r requirements.txt
```

#### 2. API密钥错误

**症状**: `APIKeyError: Invalid API key`

**排查**:
```bash
# 检查环境变量
echo $ANTHROPIC_API_KEY

# 检查keyring
python3 -c "import keyring; print(keyring.get_password('agent-chat-hub', 'ANTHROPIC_API_KEY'))"
```

**解决**:
```bash
# 重新设置API密钥
export ANTHROPIC_API_KEY="sk-ant-..."
# 或
python3 -c "import keyring; keyring.set_password('agent-chat-hub', 'ANTHROPIC_API_KEY', 'sk-ant-...')"
```

#### 3. 内存不足

**症状**: `MemoryError` 或应用被OOM killer杀死

**排查**:
```bash
# 检查内存使用
free -h

# 检查应用内存
ps aux | grep python3
```

**解决**:
```bash
# 减少并发Agent数
# 编辑 config/config.json
{
  "max_concurrent_agents": 3  # 降低到3
}

# 或增加系统内存
```

#### 4. 日志文件过大

**症状**: 磁盘空间不足

**排查**:
```bash
# 检查日志大小
du -sh logs/

# 检查磁盘空间
df -h
```

**解决**:
```bash
# 清理旧日志
find logs/ -name "*.log" -mtime +7 -delete

# 或配置日志轮转（见上文日志配置）
```

---

## 性能优化

### 1. 使用CLI工具优先

CLI工具（Claude CLI, Codex CLI, Gemini CLI）比HTTP API更快：

```bash
# 安装CLI工具
npm install -g @anthropic-ai/claude-cli
npm install -g openai-cli
# ...

# 验证CLI可用
claude --version
codex --version
```

### 2. 调整并发数

根据系统资源调整：

```json
{
  "max_concurrent_agents": 5  // 2GB RAM: 3, 4GB RAM: 5, 8GB+ RAM: 10
}
```

### 3. 启用缓存

编辑 `config/config.json`:

```json
{
  "models": {
    "claude-sonnet": {
      "extra_params": {
        "cache_control": true  // 启用prompt caching
      }
    }
  }
}
```

### 4. 优化日志级别

生产环境使用INFO或WARNING：

```json
{
  "log_level": "WARNING"  // DEBUG会影响性能
}
```

### 5. 定期清理

```bash
# 添加到crontab
crontab -e

# 每天凌晨清理7天前的日志
0 0 * * * find /path/to/agent-chat-hub/logs/ -name "*.log" -mtime +7 -delete

# 每周清理旧session
0 0 * * 0 find ~/.agent-chat-hub/sessions/ -mtime +30 -delete
```

---

## 升级指南

### 小版本升级 (v1.0.0 -> v1.0.1)

```bash
# 1. 备份配置
cp -r config/ config.backup/

# 2. 停止应用
sudo systemctl stop agent-chat-hub

# 3. 拉取新代码
git pull origin main

# 4. 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 5. 运行测试
pytest tests/unit/ -v

# 6. 启动应用
sudo systemctl start agent-chat-hub

# 7. 验证
sudo systemctl status agent-chat-hub
```

### 大版本升级 (v1.x -> v2.x)

参考 `CHANGELOG.md` 中的迁移指南。

---

## 监控脚本

创建 `scripts/monitor.sh`:

```bash
#!/bin/bash

# 检查应用状态
check_status() {
    if systemctl is-active --quiet agent-chat-hub; then
        echo "✓ 应用运行中"
    else
        echo "✗ 应用未运行"
        return 1
    fi
}

# 检查内存
check_memory() {
    MEMORY=$(ps aux | grep "[p]ython3 main.py" | awk '{print $6}')
    echo "内存使用: ${MEMORY}KB"
    
    if [ "$MEMORY" -gt 1048576 ]; then  # >1GB
        echo "⚠ 内存使用过高"
    fi
}

# 检查磁盘
check_disk() {
    USAGE=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')
    echo "磁盘使用: ${USAGE}%"
    
    if [ "$USAGE" -gt 80 ]; then
        echo "⚠ 磁盘空间不足"
    fi
}

# 检查错误日志
check_errors() {
    ERRORS=$(tail -100 logs/error.log 2>/dev/null | wc -l)
    echo "最近100行错误: ${ERRORS}条"
    
    if [ "$ERRORS" -gt 10 ]; then
        echo "⚠ 错误日志较多"
        tail -5 logs/error.log
    fi
}

# 主函数
main() {
    echo "=== Agent Chat Hub 监控 ==="
    echo "时间: $(date)"
    echo ""
    
    check_status
    check_memory
    check_disk
    check_errors
    
    echo ""
    echo "==========================="
}

main
```

使用:
```bash
chmod +x scripts/monitor.sh
./scripts/monitor.sh
```

---

**部署支持**: support@example.com  
**文档版本**: v1.0  
**最后更新**: 2026-09-06
