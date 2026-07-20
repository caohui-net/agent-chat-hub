# Syntax Highlight Plugin - 代码语法高亮插件

## 功能

为Agent Chat Hub的TUI界面提供代码语法高亮显示：
- **自动语言检测**：智能识别Python、JavaScript、TypeScript、Bash、JSON等
- **多种主题**：支持monokai、github-dark、nord、dracula主题
- **行号显示**：可选的行号显示功能

## 配置

```json
{
  "theme": "monokai",
  "line_numbers": true,
  "auto_detect": true
}
```

- `theme`: 语法高亮主题（monokai/github-dark/nord/dracula）
- `line_numbers`: 是否显示行号
- `auto_detect`: 是否自动检测代码语言

## 使用方法

### 编程方式

```python
from plugins.syntax_highlight_plugin import SyntaxHighlightPlugin

# 初始化插件
plugin = SyntaxHighlightPlugin(plugin_api)

# 高亮Python代码
code = '''
def hello(name):
    print(f"Hello, {name}!")
'''
syntax = plugin.highlight_code(code, language="python")

# 自动检测语言
syntax = plugin.highlight_code(code)  # 自动检测为Python

# 在TUI中显示（通过Rich Console）
from rich.console import Console
console = Console()
console.print(syntax)
```

### 支持的语言

自动检测支持：
- Python
- JavaScript
- TypeScript
- Bash/Shell
- JSON

手动指定可支持Pygments支持的所有语言。

## 主题预览

### Monokai（默认）
```python
# 深色主题，高对比度
def example():
    return "monokai"
```

### GitHub Dark
```python
# GitHub风格的深色主题
def example():
    return "github-dark"
```

## 依赖

- `rich`: TUI渲染和语法高亮
- `pygments`: 语法高亮引擎（Rich内部使用）

## 版本

- **当前版本**: 1.0.0
- **最后更新**: 2026-07-20
