# UI改进说明 - 文件预览返回与面板宽度调整

## 修复的问题

### 1. ✅ 文件预览后无法返回聊天界面

**问题描述**: 点击"📝 查看内容"后，聊天区显示文件内容，但无法返回原来的聊天历史。

**解决方案**:
- 添加聊天历史备份机制 (`chat_history_backup`)
- 查看文件前自动备份当前聊天显示内容
- 提供两种返回方式：
  - **按钮**: 新增 `↩️ 返回聊天` 按钮
  - **快捷键**: `Ctrl+B` 快速返回

**实现细节**:
```python
# 备份当前内容
self.chat_history_backup = chat_display.renderable

# 恢复备份内容
def action_restore_chat(self):
    if self.chat_history_backup:
        chat_display.update(self.chat_history_backup)
        self.chat_history_backup = ""
```

### 2. ✅ 面板宽度可调整

**问题描述**: Agent面板和文件面板宽度固定，无法根据需求调整。

**解决方案**:
- 为Agent面板和文件面板添加 `min-width` 和 `max-width`
- 允许面板在一定范围内调整宽度
- 聊天区使用 `1fr` 自适应剩余空间

**CSS配置**:
```css
#agent_panel {
    width: 30;
    min-width: 20;  /* 最小20列 */
    max-width: 50;  /* 最大50列 */
}

#file_panel {
    width: 35;
    min-width: 25;  /* 最小25列 */
    max-width: 60;  /* 最大60列 */
}

#chat_container {
    width: 1fr;  /* 自适应剩余空间 */
}
```

## 新增功能

### 返回聊天功能

**触发方式**:
1. **按钮**: 点击右侧 `↩️ 返回聊天` 按钮
2. **快捷键**: 按 `Ctrl+B`

**行为**:
- 如果有备份：恢复查看文件前的聊天内容
- 如果无备份：显示当前会话的消息历史
- 如果无历史：显示欢迎消息

### 用户体验改进

**文件预览提示**:
查看文件内容时，底部显示提示：
```
💡 提示: 按Ctrl+B返回聊天历史
```

**快捷键绑定**:
```
Ctrl+C  : 退出
Ctrl+N  : 新会话
Ctrl+B  : 返回聊天  (新增)
```

## 使用指南

### 查看文件并返回

1. 在右侧文件列表选择文件
2. 点击 `📝 查看内容`
3. 聊天区显示文件内容（前50行）
4. 返回方式任选其一：
   - 点击 `↩️ 返回聊天` 按钮
   - 按 `Ctrl+B` 键
5. 聊天区恢复原有对话内容

### 调整面板宽度

**方法1: CSS修改** (需重启)
编辑 `src/tui/app.py` 中的CSS:
```css
#agent_panel {
    width: 30;  /* 修改此值 (20-50) */
}

#file_panel {
    width: 35;  /* 修改此值 (25-60) */
}
```

**方法2: 终端窗口大小**
- 调整终端窗口宽度
- 面板会按比例自动缩放
- 中间聊天区自适应剩余空间

## 技术实现

### 新增属性
- `self.chat_history_backup: str` - 聊天历史备份

### 新增方法
- `action_restore_chat()` - 恢复聊天历史action

### 修改方法
- `on_button_pressed()` - 添加view_btn和restore_btn处理
- `compose()` - 添加"返回聊天"按钮

### CSS更新
- 添加 `min-width` 和 `max-width` 限制
- 添加 `.splitter` 样式（预留分隔符支持）

## 测试清单

- [x] 查看文件内容
- [x] 文件内容显示正确（前50行+提示）
- [x] 点击"返回聊天"按钮恢复历史
- [x] Ctrl+B快捷键恢复历史
- [x] 无备份时显示当前会话历史
- [x] Agent面板宽度限制生效
- [x] 文件面板宽度限制生效
- [x] 聊天区自适应剩余空间

## 代码统计

修改文件: `src/tui/app.py`

新增内容:
- 1个属性 (`chat_history_backup`)
- 1个action方法 (`action_restore_chat`)
- 1个按钮 (`restore_btn`)
- 1个快捷键绑定 (`Ctrl+B`)
- CSS宽度限制 (6行)

## 后续改进建议

### 面板宽度调整
1. 添加拖拽分隔符 (Splitter widget)
2. 记住用户自定义宽度
3. 支持面板折叠/展开

### 文件预览
1. 支持语法高亮（代码文件）
2. 支持二进制文件预览（图片、PDF）
3. 添加搜索功能

### 快捷键
1. 添加更多快捷键（折叠面板、切换焦点）
2. 显示快捷键帮助面板
3. 支持自定义快捷键

---

**状态**: ✅ 完成并测试  
**日期**: 2026-09-08  
**相关Issue**: 文件预览返回、面板宽度调整
