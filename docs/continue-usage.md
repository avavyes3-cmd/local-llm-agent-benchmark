# Continue 使用说明（本地 llama.cpp）

## 模型分工

当前本地 GGUF 已全部移除，Continue 不再配置本地模型。下面的历史模型名称仅用于说明此前的测试结果；重新部署模型前不要启动桌面本地服务脚本。

| Continue 角色 | 模型 | 用途 |
|---|---|---|
| Creative Chat | KrakenSakura 12B - Creative Chat (No Tools) | 低审查创作；不具备真实文件工具能力 |
| Agent / Chat / Edit / Apply | Ornith 1.5 9B - Agent + Code | 搜索、读取文件、调用工具、执行多步修改、生成或修复代码 |

## Agent 和 Edit/Apply 的区别

- **Agent** 会使用 `read_file`、`edit_existing_file`、`create_new_file` 等工具，适合要求“直接修改文件”或“新建文件”。模型应在 Agent 模式下运行。
- **Edit/Apply** 会先生成一个代码块，Continue 显示 **Apply** 按钮；点击后才写回文件。这不是模型失败，而是 Continue 的确认式编辑流程。
- 普通 Chat 只会回答文字，不会自动写文件。

## 推荐操作流程

1. 打开目标项目文件夹作为 VS Code workspace（不要只打开单个文件）。
2. 需要自动读写文件时，选择 **Agent** 模式和 `Ornith 1.5 9B - Agent + Code`。
3. 明确告诉模型目标路径和动作，例如：“使用工具读取并直接修改 `C_CPP/C++/链表反转.c`，修复编译错误，然后运行编译命令验证。”
4. 看到代码卡片时，点击 **Apply**；Apply 是 Continue 的写入确认按钮。
5. 修改配置或模型后执行 `Developer: Reload Window`，避免旧会话继续使用旧配置。

## Windows 路径注意事项

Continue 的工具路径是相对于 workspace 根目录的。若 workspace 是 `C:\Users\12706\Desktop\C_CPP`，目标文件应写成：

```text
C_CPP/C++/链表反转.c
```

而不是只写 `链表反转.c`。如果 Agent 反复提示文件不存在，先确认 VS Code 左侧打开的根目录和文件的相对路径。

## 失败排查

- 出现 500/Jinja role 错误：执行 `Developer: Reload Window`，新建 Continue 会话，并确认选择了 Ornith；不要继续提交旧模型留下的会话历史。
- 只输出代码不修改：检查是否处于 Chat/Edit 而不是 Agent；Edit 模式需要点击 Apply。
- 工具报告路径不存在：使用 workspace 相对路径，并重新打开项目根目录。
- 模型响应很慢：8GB 显存上只保持一个模型加载；Ornith 热生成约 52–65 tokens/s，但从 E: 首次冷加载约需 80 秒。
