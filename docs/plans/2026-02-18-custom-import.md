# Custom Import Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a custom Excel import wizard that allows users to map their own Excel format to system tables through a guided multi-step process.

**Architecture:** Full-screen modal dialog with 5-step wizard (file selection → template selection → sheet mapping → column mapping → confirmation). Backend provides REST APIs for file parsing, preview checking, and import execution. Templates stored in a new database table as JSON config.

**Tech Stack:** Flask, SQLAlchemy, openpyxl, vanilla JavaScript, CSS

---

## Phase 1: Database Model and Basic API

### Task 1: Create ImportTemplate Model

**Files:**
- Modify: `models.py`

**Step 1: Add ImportTemplate model to models.py**

Add after the existing model definitions (around line 200):

```python
class ImportTemplate(db.Model):
  """自定义导入模板"""
  __tablename__ = 'import_template'

  id = db.Column(Integer, primary_key=True, comment='主键')
  name = db.Column(String(100), nullable=False, comment='模板名称')
  config = db.Column(JSON, nullable=False, comment='映射配置')
  created_at = db.Column(DateTime, default=datetime.utcnow, comment='创建时间')
  updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')

  def __repr__(self):
    return f'<ImportTemplate {self.id}: {self.name}>'
```

Add import at the top of the file:
```python
from sqlalchemy import String, Integer, Float, Boolean, Date, ForeignKey, JSON, DateTime
from datetime import datetime
```

**Step 2: Create database migration**

Run:
```bash
source myenv/bin/activate && python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

**Step 3: Commit**

```bash
git add models.py
git commit -m "feat: add ImportTemplate model for custom import templates"
```

---

### Task 2: Add System Tables Configuration

**Files:**
- Create: `utils/system_tables.py`

**Step 1: Create system_tables.py with table definitions**

See design document `docs/plans/2026-02-18-custom-import-design.md` for full SYSTEM_TABLES configuration.

**Step 2: Commit**

```bash
git add utils/system_tables.py
git commit -m "feat: add system tables configuration for custom import"
```

---

### Task 3: Add Template CRUD API

**Files:**
- Modify: `routes/api.py`
- Create: `tests/test_custom_import_api.py`

**Step 1: Write tests for template API (TDD)**

**Step 2: Run tests to verify they fail**

**Step 3: Add template API endpoints**

**Step 4: Run tests to verify they pass**

**Step 5: Commit**

See detailed code in design document.

---

### Task 4: Add Excel Parse API

**Files:**
- Modify: `routes/api.py`
- Modify: `tests/test_custom_import_api.py`

Follow TDD process: write test → verify fail → implement → verify pass → commit.

---

## Phase 2: Preview and Execute API

### Task 5: Add Preview API

Implement preview endpoint with conflict detection.

### Task 6: Add Execute Import API

Implement execute endpoint with data import logic.

---

## Phase 3: Frontend Modal and Basic UI

### Task 7: Add Custom Import Modal to system.html

Add modal HTML structure and CSS styles.

### Task 8: Create custom-import.js Module

Create JavaScript wizard module with steps 1-3.

---

## Phase 4: Complete Implementation

### Task 9: Implement Column Mapping UI (Step 4)

### Task 10: Implement Preview API Integration

### Task 11: Implement Execute Import UI (Step 5)

### Task 12: Implement Carriage Merged Cell Detection

---

## Phase 5: Testing and Documentation

### Task 13: Run Full Test Suite

### Task 14: Update Documentation

Update CLAUDE.md, README.md, and design documents.

---

## Implementation Notes

1. **Use textContent instead of innerHTML** for all user-provided content to prevent XSS
2. **Follow existing code style** - 2 space indentation, camelCase variables
3. **Test database isolation** - Use TestConfig for tests
4. **Browser compatibility** - Test on Chrome, Edge, Safari

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1 | 1-4 | Database model, system tables config, template API, parse API |
| Phase 2 | 5-6 | Preview API, execute API |
| Phase 3 | 7-8 | Frontend modal, JavaScript wizard |
| Phase 4 | 9-12 | Complete column mapping and execute steps |
| Phase 5 | 13-14 | Full testing, documentation update |

**Total estimated commits: ~12-15**

For detailed code and step-by-step instructions, refer to the design document: `docs/plans/2026-02-18-custom-import-design.md`
