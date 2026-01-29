# 工作流参考

> 此文件包含 ai-partner-chat skill 的工作流和最佳实践。核心规则见 [SKILL.md](../SKILL.md)

## Conversation Workflow

For each user query, follow this process:

### Load Personas

Read both persona files to understand:
- User's background, preferences, and communication style
- AI's role definition and interaction guidelines

### Retrieve Relevant Notes

Query the vector database for top 5 semantically similar notes:

```bash
python scripts/query_notes.py "user query text" --top-k 5
```

### Construct Context

Combine:
1. **User Persona**: Background, preferences, expertise
2. **AI Persona**: Role, communication style, guidelines
3. **Relevant Notes** (top 5): User's previous thoughts and knowledge
4. **Current Conversation**: Ongoing chat history

### Generate Response

Synthesize a response that:
- Aligns with both persona definitions
- Naturally references relevant notes when applicable
- Maintains continuity with user's knowledge base

**When Referencing Notes:**
- Use natural phrasing: "Based on your previous note about..."
- Make connections: "This relates to what you mentioned in..."
- Avoid robotic citations: integrate context smoothly

---

## Maintenance

### Adding New Notes

```bash
python scripts/add_note.py /path/to/new_note.md
```

### Reinitializing Database

```bash
python scripts/init_vector_db.py /path/to/notes --db-path ./vector_db
```

---

## Best Practices

### Persona Design

- **Be Specific**: Vague personas lead to generic responses
- **Include Examples**: Show desired interaction patterns
- **Update Regularly**: Refine based on conversation quality

### Note Management

- **Any Format Welcome**: AI Agent approach adapts to your note structure
- **Meaningful Content**: Rich, substantive notes yield better retrieval
- **Rebuild When Needed**: Re-index when note collection changes significantly

### Time Expression in Memory Files

**Critical Rule**: Never use relative time in memory files.

| Wrong | Right |
|-------|-------|
| "2周前提离职" | "2026年1月中旬提离职" |
| "昨天聊过" | "2026-01-26 聊过" |
| "最近在做" | "2026年1月在做" |

**Why**: Relative time becomes inaccurate as time passes.

### Context Integration

- **Natural References**: Only reference when genuinely relevant
- **Connection Quality**: Prioritize meaningful connections over quantity
- **Conversation Flow**: Don't let note references disrupt natural dialogue

---

## 公众号剪藏工作流

**目的**：将微信公众号文章转化为可检索的周报素材

**工具**：Obsidian Web Clipper（浏览器插件）

**分工**：
| 谁 | 做什么 |
|----|-------|
| 99 | 剪藏文章 + 写一句insight |
| 9维斯 | 写summary + 加tags + 入素材库 |

**99操作流程**：
1. 微信电脑端打开公众号文章 → 复制链接 → 浏览器打开
2. 点击Web Clipper插件 → 保存到 `notes/Clippings/`
3. 剪藏时顺手写一句insight（可选）
4. 告诉9维斯"帮我处理一下"

**9维斯处理流程**：
1. 检查 `notes/Clippings/` 下的新文件
2. 读取文章内容，生成summary
3. 更新原文frontmatter（tags + 适用板块）
4. 添加callout到正文顶部
5. 在素材库添加条目

**批量处理**：
- 99可以一次剪藏多篇，然后说"更新未更新的"
- 9维斯批量处理缺少tags/summary的文件

**文件名特殊字符注意**：
- Web Clipper可能生成含中文引号（""）的文件名
- 处理时用Python的os.listdir()遍历，避免直接拼接路径
