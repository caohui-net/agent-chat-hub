# 故障排除指南

## 🐛 文件预览问题

### 问题: 点击"查看内容"后应用崩溃退出

**已修复** (最新版本)

**症状**: 
- 点击 `📝 查看内容` 按钮
- 应用直接退出，没有错误提示

**原因**: 
- 文件读取异常未完全捕获
- 备份聊天历史时类型转换问题

**解决方案**:
```bash
# 拉取最新代码
git pull

# 重启应用
./start.sh
```

**如果问题仍存在**:
1. 运行测试脚本验证:
   ```bash
   python3 test_file_view.py
   ```
2. 按提示操作，观察是否有错误信息
3. 如果看到错误信息而非崩溃，说明修复生效

---

## 🔧 常见问题

### 1. 找不到 start.sh

**症状**:
```bash
$ ./start.sh
bash: ./start.sh: 没有那个文件或目录
```

**原因**: 不在项目根目录

**解决**:
```bash
# 确认当前位置
pwd

# 进入项目根目录
cd /home/caohui/orca/workspaces/agent-chat-hub/agent-chat-hub

# 验证文件存在
ls start.sh

# 启动
./start.sh
```

---

### 2. 虚拟环境不存在

**症状**:
```bash
错误: 虚拟环境不存在
```

**解决**:
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -e .

# 启动
./start.sh
```

---

### 3. 文件浏览器无法打开

**症状**: 点击 `📤 浏览上传` 无反应

**可能原因**:
- Textual版本不兼容
- 终端不支持

**解决**:
```bash
# 检查Textual版本
pip show textual

# 更新到最新版
pip install --upgrade textual

# 重启应用
./start.sh
```

---

### 4. 文件上传后列表不显示

**症状**: 选择文件后，右侧列表空白

**检查**:
```python
# 验证文件是否真的上传了
# 在应用中按Ctrl+C退出
# 查看uploaded_files列表
```

**临时解决**: 重启应用

---

### 5. 无法返回聊天历史

**症状**: 按 `Ctrl+B` 或点击 `↩️ 返回聊天` 无效

**可能原因**:
- 没有备份历史（首次使用）
- 备份为空

**解决**:
- 先与Agent对话产生历史
- 再查看文件
- 然后返回就会有内容

**验证**:
```bash
# 查看是否有聊天历史
# 在聊天区应该有对话记录
```

---

### 6. 文件编码错误

**症状**: 
```
❌ 文件编码错误（非UTF-8）
```

**原因**: 文件不是UTF-8编码

**解决**:
```bash
# 转换文件编码
iconv -f GB18030 -t UTF-8 原文件.txt > 新文件.txt

# 或使用其他编码
iconv -f GBK -t UTF-8 原文件.txt > 新文件.txt
```

---

### 7. 大文件无法预览

**症状**: 
```
📄 文件过大，仅显示路径
```

**原因**: 文件大于1MB

**这是正常行为**: 
- 大文件仅显示路径
- 避免内存溢出
- 不是错误

---

## 🧪 调试模式

### 启用详细日志

编辑 `main.py`:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### 查看错误详情

如果应用崩溃，查看traceback:
```bash
./start.sh 2>&1 | tee app.log
```

崩溃后查看 `app.log` 文件。

---

## 🆘 报告问题

如果以上方法都无法解决，请提供：

1. **错误信息**: 完整的错误输出
2. **操作步骤**: 如何重现问题
3. **环境信息**:
   ```bash
   python3 --version
   pip show textual
   uname -a
   ```
4. **文件信息** (如果是文件相关):
   ```bash
   file 文件路径
   ls -lh 文件路径
   ```

---

## 📞 快速诊断

运行诊断脚本:
```bash
python3 test_file_view.py
```

这会：
- 验证导入是否正常
- 创建测试文件
- 提供测试步骤

---

**最后更新**: 2026-09-08  
**版本**: v1.1 (包含文件预览修复)
