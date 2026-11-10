PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL CHECK(length(name) BETWEEN 2 AND 100),
 email TEXT NOT NULL COLLATE NOCASE UNIQUE,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL DEFAULT 'visitor' CHECK(role IN ('visitor','admin')),
 created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS works (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL, author TEXT NOT NULL, year INTEGER,
 category TEXT NOT NULL, room TEXT NOT NULL, description TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL, kind TEXT NOT NULL,
 starts_at TEXT NOT NULL, duration_minutes INTEGER NOT NULL CHECK(duration_minutes>0),
 capacity INTEGER NOT NULL CHECK(capacity>0),
 description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','cancelled'))
);
CREATE TABLE IF NOT EXISTS bookings (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
 seats INTEGER NOT NULL CHECK(seats BETWEEN 1 AND 6),
 status TEXT NOT NULL DEFAULT 'confirmed' CHECK(status IN ('confirmed','cancelled')),
 created_at TEXT NOT NULL DEFAULT (datetime('now')),
 UNIQUE(user_id,event_id)
);
CREATE TABLE IF NOT EXISTS feedback (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
 rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
 comment TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL DEFAULT (datetime('now')),
 UNIQUE(user_id,event_id)
);
CREATE TABLE IF NOT EXISTS sessions (
 token_hash TEXT PRIMARY KEY,
 user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 expires_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(starts_at);
CREATE INDEX IF NOT EXISTS idx_bookings_event_status ON bookings(event_id,status);
CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
