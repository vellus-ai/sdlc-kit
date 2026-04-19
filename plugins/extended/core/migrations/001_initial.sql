-- core/migrations/001_initial.sql
-- Migração inicial: criação das tabelas fundamentais do SDLC Kit

CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    title TEXT,
    phase TEXT,
    type TEXT,
    status TEXT,
    created TEXT,
    updated TEXT,
    mtime REAL,
    frontmatter_json TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER REFERENCES notes(id),
    event_type TEXT NOT NULL,
    ts TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL REFERENCES notes(id),
    target_title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER REFERENCES notes(id),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    epic TEXT,
    milestone TEXT,
    phase TEXT,
    branch TEXT,
    created TEXT DEFAULT (datetime('now')),
    due TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id INTEGER REFERENCES notes(id),
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed',
    context TEXT
);

CREATE TABLE IF NOT EXISTS worktrees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch TEXT NOT NULL UNIQUE,
    path TEXT NOT NULL,
    base_branch TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    status TEXT NOT NULL DEFAULT 'active',
    task_id INTEGER REFERENCES tasks(id),
    agent_active INTEGER DEFAULT 0,
    pr_number INTEGER,
    pr_status TEXT,
    pr_url TEXT
);
