# Agent Chat Hub - 运维指南

## 1. 系统服务配置

### 1.1 systemd服务

创建systemd服务单元文件，使应用作为系统服务运行。

**创建服务文件**：

```bash
sudo nano /etc/systemd/system/agent-chat-hub.service
```

**服务配置**：

```ini
[Unit]
Description=Agent Chat Hub - Multi-model AI Agent Chat System
After=network.target

[Service]
Type=simple
User=agent-hub
Group=agent-hub
WorkingDirectory=/opt/agent-chat-hub
Environment="PATH=/opt/agent-chat-hub/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/opt/agent-chat-hub"
EnvironmentFile=/etc/agent-chat-hub/env

ExecStart=/opt/agent-chat-hub/.venv/bin/python main.py
ExecReload=/bin/kill -HUP $MAINPID

Restart=always
RestartSec=10

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=agent-chat-hub

# 资源限制
LimitNOFILE=65536
LimitNPROC=4096

# 安全强化
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/agent-chat-hub/sessions /var/log/agent-chat-hub

[Install]
WantedBy=multi-user.target
```

**操作命令**：

```bash
# 重载systemd配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start agent-chat-hub

# 停止服务
sudo systemctl stop agent-chat-hub

# 重启服务
sudo systemctl restart agent-chat-hub

# 设置开机启动
sudo systemctl enable agent-chat-hub

# 查看状态
sudo systemctl status agent-chat-hub

# 查看日志
sudo journalctl -u agent-chat-hub -f
```

### 1.2 环境变量配置

创建 `/etc/agent-chat-hub/env` 文件：

```bash
# API密钥
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# 日志级别
LOG_LEVEL=INFO

# 配置目录
CONFIG_DIR=/etc/agent-chat-hub/config

# 会话存储
SESSION_DIR=/var/lib/agent-chat-hub/sessions
```

---

## 2. 日志管理

### 2.1 日志配置

**日志位置**：

| 日志类型 | 位置 | 说明 |
|---------|------|------|
| 应用日志 | `/var/log/agent-chat-hub/app.log` | 应用主日志 |
| 错误日志 | `/var/log/agent-chat-hub/error.log` | 错误和异常 |
| 访问日志 | `/var/log/agent-chat-hub/access.log` | API访问日志 |
| systemd日志 | `journalctl -u agent-chat-hub` | 系统服务日志 |

**日志级别**：

- `DEBUG` - 详细调试信息
- `INFO` - 一般信息（推荐生产环境）
- `WARNING` - 警告信息
- `ERROR` - 错误信息
- `CRITICAL` - 严重错误

### 2.2 日志轮转

创建 `/etc/logrotate.d/agent-chat-hub`：

```
/var/log/agent-chat-hub/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 agent-hub agent-hub
    sharedscripts
    postrotate
        systemctl reload agent-chat-hub > /dev/null 2>&1 || true
    endscript
}
```

### 2.3 日志查询

```bash
# 实时查看日志
tail -f /var/log/agent-chat-hub/app.log

# 查看最近100行
tail -n 100 /var/log/agent-chat-hub/app.log

# 查看错误日志
grep ERROR /var/log/agent-chat-hub/app.log

# 使用journalctl
journalctl -u agent-chat-hub --since "1 hour ago"
journalctl -u agent-chat-hub --since "2024-01-01" --until "2024-01-02"
```

---

## 3. 监控和告警

### 3.1 健康检查

**HTTP健康检查端点**（如果启用了HTTP插件）：

```bash
# 基础健康检查
curl http://localhost:8000/health

# 返回示例
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 3600,
  "active_sessions": 5
}
```

### 3.2 系统监控指标

**关键指标**：

| 指标 | 说明 | 正常范围 |
|------|------|---------|
| CPU使用率 | 进程CPU占用 | <50% |
| 内存使用 | RSS内存 | <2GB |
| 活跃会话数 | 当前会话数 | <100 |
| 消息队列长度 | MessageBus队列 | <100 |
| 响应时间 | Agent响应延迟 | <5s |

**监控脚本示例**：

```bash
#!/bin/bash
# monitor.sh - 系统监控脚本

# 检查进程是否运行
if ! systemctl is-active --quiet agent-chat-hub; then
    echo "ALERT: Service is not running"
    # 发送告警
    exit 1
fi

# 检查内存使用
MEM_USAGE=$(ps aux | grep agent-chat-hub | grep -v grep | awk '{print $4}')
if (( $(echo "$MEM_USAGE > 80" | bc -l) )); then
    echo "ALERT: High memory usage: $MEM_USAGE%"
fi

# 检查日志错误
ERROR_COUNT=$(grep -c ERROR /var/log/agent-chat-hub/app.log | tail -100)
if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "ALERT: High error count: $ERROR_COUNT"
fi
```

### 3.3 Prometheus监控（可选）

**暴露Prometheus指标**：

如果使用Prometheus，可以添加metrics端点：

```python
# src/plugins/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
requests_total = Counter('agent_requests_total', 'Total agent requests')
request_duration = Histogram('agent_request_duration_seconds', 'Request duration')
active_sessions = Gauge('active_sessions', 'Number of active sessions')
```

**Prometheus配置**：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'agent-chat-hub'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

---

## 4. 备份和恢复

### 4.1 备份策略

**需要备份的内容**：

1. **配置文件**
   - `~/.agent-chat-hub/config/`
   - `/etc/agent-chat-hub/`

2. **会话数据**
   - `~/.agent-chat-hub/sessions/`
   - `/var/lib/agent-chat-hub/sessions/`

3. **日志文件**（可选）
   - `/var/log/agent-chat-hub/`

**备份脚本**：

```bash
#!/bin/bash
# backup.sh - 数据备份脚本

BACKUP_DIR="/var/backups/agent-chat-hub"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.tar.gz"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份数据
tar -czf "$BACKUP_FILE" \
    /etc/agent-chat-hub/ \
    /var/lib/agent-chat-hub/sessions/ \
    ~/.agent-chat-hub/config/

# 保留最近30天的备份
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

**自动备份（cron）**：

```bash
# 编辑crontab
crontab -e

# 每天凌晨3点备份
0 3 * * * /opt/agent-chat-hub/scripts/backup.sh
```

### 4.2 恢复流程

```bash
# 停止服务
sudo systemctl stop agent-chat-hub

# 恢复备份
tar -xzf /var/backups/agent-chat-hub/backup_20260726_030000.tar.gz -C /

# 验证配置
ls /etc/agent-chat-hub/config/

# 启动服务
sudo systemctl start agent-chat-hub

# 检查状态
sudo systemctl status agent-chat-hub
```

---

## 5. 性能调优

### 5.1 Python运行时优化

**环境变量**：

```bash
# 禁用Python断言（生产环境）
export PYTHONOPTIMIZE=2

# 使用更快的JSON库
pip install orjson
```

**配置调整**：

```python
# config/performance.json
{
  "budget_limits": {
    "max_agents": 3,
    "max_calls_per_round": 5,
    "max_tokens": 15000,
    "timeout_seconds": 120
  },
  "message_bus": {
    "queue_maxsize": 1000,
    "max_history": 100
  }
}
```

### 5.2 系统资源限制

**调整文件描述符限制**：

```bash
# 编辑 /etc/security/limits.conf
agent-hub soft nofile 65536
agent-hub hard nofile 65536

# 或在systemd服务文件中设置
LimitNOFILE=65536
```

### 5.3 并发优化

**调整异步并发数**：

```python
# src/agents/executor.py
async def execute_concurrent(self, agents, messages, max_concurrent=10):
    """限制并发数避免资源耗尽"""
    semaphore = asyncio.Semaphore(max_concurrent)
    # ...
```

---

## 6. 安全加固

### 6.1 API密钥管理

**使用密钥管理服务**：

```python
# 使用keyring存储密钥
import keyring

# 存储
keyring.set_password("agent-chat-hub", "OPENAI_API_KEY", "sk-...")

# 读取
api_key = keyring.get_password("agent-chat-hub", "OPENAI_API_KEY")
```

**环境变量保护**：

```bash
# 限制环境文件权限
chmod 600 /etc/agent-chat-hub/env
chown agent-hub:agent-hub /etc/agent-chat-hub/env
```

### 6.2 网络安全

**防火墙配置**：

```bash
# 只允许本地访问API端口
sudo ufw allow from 127.0.0.1 to any port 8000
sudo ufw deny 8000

# 或使用iptables
sudo iptables -A INPUT -p tcp --dport 8000 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j DROP
```

**HTTPS配置**（如果对外暴露）：

使用Nginx反向代理：

```nginx
# /etc/nginx/sites-available/agent-chat-hub
server {
    listen 443 ssl http2;
    server_name agent-hub.example.com;

    ssl_certificate /etc/ssl/certs/agent-hub.crt;
    ssl_certificate_key /etc/ssl/private/agent-hub.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 6.3 访问控制

**基础认证**：

```python
# 添加认证中间件
from functools import wraps

def require_auth(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not validate_token(token):
            return {"error": "Unauthorized"}, 401
        return await f(*args, **kwargs)
    return decorated_function
```

---

## 7. 故障排查

### 7.1 常见问题

**服务无法启动**：

```bash
# 检查服务状态
sudo systemctl status agent-chat-hub

# 查看详细日志
sudo journalctl -xe -u agent-chat-hub

# 检查配置文件
python -c "import json; json.load(open('config/agents.json'))"
```

**内存占用过高**：

```bash
# 查看进程内存
ps aux | grep agent-chat-hub

# 使用memory_profiler
pip install memory-profiler
python -m memory_profiler main.py
```

**响应缓慢**：

```bash
# 检查系统负载
uptime
top

# 检查网络连接
netstat -an | grep 8000

# 运行性能基准
python benchmarks/benchmark_phase2.py
```

### 7.2 日志分析

**查找错误模式**：

```bash
# 统计错误类型
grep ERROR /var/log/agent-chat-hub/app.log | awk '{print $5}' | sort | uniq -c

# 查找超时问题
grep "timeout" /var/log/agent-chat-hub/app.log

# 查找内存相关错误
grep -i "memory\|oom" /var/log/agent-chat-hub/app.log
```

---

## 8. 升级和维护

### 8.1 升级流程

```bash
# 1. 备份数据
/opt/agent-chat-hub/scripts/backup.sh

# 2. 停止服务
sudo systemctl stop agent-chat-hub

# 3. 拉取新版本
cd /opt/agent-chat-hub
git pull origin main

# 4. 更新依赖
source .venv/bin/activate
pip install -e ".[dev]"

# 5. 运行数据库迁移（如果有）
python scripts/migrate.py

# 6. 启动服务
sudo systemctl start agent-chat-hub

# 7. 验证
sudo systemctl status agent-chat-hub
curl http://localhost:8000/health
```

### 8.2 维护窗口

建议在低峰期执行维护操作：

- 凌晨2:00-4:00（用户活跃度最低）
- 提前通知用户（如果是公共服务）
- 准备回滚方案

---

## 9. 容器化部署（Docker）

### 9.1 Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  agent-chat-hub:
    image: agent-chat-hub:latest
    container_name: agent-chat-hub
    restart: always
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./config:/app/config
      - ./sessions:/app/sessions
      - ./logs:/var/log/agent-chat-hub
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**运行**：

```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 9.2 Kubernetes部署

参考 `k8s/` 目录下的配置文件（如果有）。

---

## 10. 监控告警集成

### 10.1 集成Grafana

如果使用Prometheus + Grafana：

1. 添加Prometheus数据源
2. 导入Agent Chat Hub dashboard
3. 配置告警规则

**告警示例**：

```yaml
# alerting_rules.yml
groups:
  - name: agent-chat-hub
    rules:
      - alert: HighErrorRate
        expr: rate(agent_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          
      - alert: ServiceDown
        expr: up{job="agent-chat-hub"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
```

---

## 11. 参考资源

- [DEPLOYMENT.md](DEPLOYMENT.md) - 部署指南
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 故障排除
- [systemd文档](https://www.freedesktop.org/software/systemd/man/)
- [Prometheus监控](https://prometheus.io/docs/)

---

**文档版本**：v1.0  
**最后更新**：2026-07-26  
**维护者**：Agent Chat Hub Team
