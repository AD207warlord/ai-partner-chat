# 技术设置指南

> 此文件包含 ai-partner-chat skill 的初始设置和技术细节。核心规则见 [SKILL.md](../SKILL.md)

## Prerequisites

Before first use, complete these steps in order:

1. **Create directory structure**
   ```bash
   mkdir -p config notes vector_db scripts
   ```

2. **Set up Python environment**
   ```bash
   python3 -m venv venv
   ./venv/bin/pip install -r .claude/skills/ai-partner-chat/scripts/requirements.txt
   ```
   Note: First run will download embedding model (~4.3GB)

3. **Generate persona templates**
   Copy from `.claude/skills/ai-partner-chat/assets/` to `config/`:
   - `user-persona-template.md` → `config/user-persona.md`
   - `ai-persona-template.md` → `config/ai-persona.md`

4. **User adds notes**
   Place markdown notes in `notes/` directory (any format/structure)

5. **Initialize vector database** (see section below)

---

## Initial Setup

### Create Persona Files

**User Persona** (`user-persona.md`):
- Define user's background, expertise, interests
- Specify communication preferences and working style
- Include learning goals and current projects

**AI Persona** (`ai-persona.md`):
- Define AI's role and expertise areas
- Specify communication style and tone
- Set interaction guidelines and response strategies

### Initialize Vector Database

This skill uses **AI Agent approach** for intelligent note chunking:

**When you initialize the vector database, Claude Code will:**
1. Read notes from `<project_root>/notes/` directory
2. **Analyze each note's format** (daily logs, structured docs, continuous text, etc.)
3. **Generate custom chunking code** tailored to that specific note
4. Execute the code to produce chunks conforming to `chunk_schema.Chunk` format
5. Generate embeddings using **BAAI/bge-m3** (optimized for Chinese text)
6. Store in ChromaDB at `<project_root>/vector_db/`

**Chunk Format Requirement:**
```python
{
    'content': 'chunk text content',
    'metadata': {
        'filename': 'note.md',       # Required
        'filepath': '/path/to/file', # Required
        'chunk_id': 0,               # Required
        'chunk_type': 'date_entry',  # Required
        'date': '2025-11-07',        # Optional
        'title': 'Section title',    # Optional
    }
}
```

**Execute**: `./venv/bin/python scripts/chunk_and_index.py`

---

## Technical Details

### Data Architecture

**User data is stored in project root**, not inside the skill directory:

```
<project_root>/
├── notes/                      # User's markdown notes
├── vector_db/                  # ChromaDB vector database
├── venv/                       # Python dependencies
├── config/
│   ├── user-persona.md
│   └── ai-persona.md
└── .claude/skills/ai-partner-chat/
    ├── SKILL.md
    ├── docs/
    └── scripts/
```

**Design principles:**
- ✅ User data (notes, personas, vectors) lives in project root
- ✅ Easy to backup, migrate, or share across skills
- ✅ Skill code is stateless and replaceable

### Vector Database

- **Storage**: ChromaDB (persistent local storage)
- **Embedding Model**: BAAI/bge-m3 (multilingual, optimized for Chinese)
- **Similarity Metric**: Cosine similarity
- **Chunking**: AI-generated custom code per note

### Scripts

- `chunk_schema.py`: Chunk format specification
- `vector_indexer.py`: Embedding generation and ChromaDB indexing
- `vector_utils.py`: Query utilities
- `requirements.txt`: Python dependencies

---

## Troubleshooting

**Database Connection Errors:**
- Ensure `<project_root>/vector_db/` directory exists and is writable
- Check that Python dependencies are installed in venv

**Poor Retrieval Quality:**
- Try re-indexing with Claude Code analyzing notes fresh
- Verify notes contain substantial content (not just titles)
- Consider increasing `top_k` value for more context

**Chunking Issues:**
- If chunks are too large/small, ask Claude to adjust chunking strategy
- Review generated chunking code and provide feedback
