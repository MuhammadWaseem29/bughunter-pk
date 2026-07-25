import sqlite3
import json
from datetime import datetime
from typing import Optional


DB_PATH = "bughunter.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            reporter TEXT NOT NULL,
            organization TEXT DEFAULT '',
            description TEXT NOT NULL,
            steps_to_reproduce TEXT DEFAULT '',
            severity TEXT DEFAULT 'Pending',
            severity_score INTEGER DEFAULT 0,
            category TEXT DEFAULT 'Unknown',
            owasp_top10 TEXT DEFAULT '',
            risk_score INTEGER DEFAULT 0,
            fix_suggestion TEXT DEFAULT '{}',
            risk_analysis TEXT DEFAULT '{}',
            status TEXT DEFAULT 'Open',
            language TEXT DEFAULT 'en',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def insert_report(title: str, reporter: str, organization: str,
                  description: str, steps: str, language: str = "en") -> int:
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO reports (title, reporter, organization, description,
                           steps_to_reproduce, language)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, reporter, organization, description, steps, language))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def update_report_analysis(report_id: int, analysis: dict):
    conn = get_connection()
    severity = analysis.get("severity", {})
    category = analysis.get("category", {})
    fix = analysis.get("fix", {})
    risk = analysis.get("risk", {})

    conn.execute("""
        UPDATE reports SET
            severity = ?,
            severity_score = ?,
            category = ?,
            owasp_top10 = ?,
            risk_score = ?,
            fix_suggestion = ?,
            risk_analysis = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        severity.get("severity", "Unknown"),
        severity.get("score", 0),
        category.get("primary_category", "Unknown"),
        category.get("owasp_top10", ""),
        risk.get("risk_score", 0),
        json.dumps(fix),
        json.dumps(risk),
        report_id
    ))
    conn.commit()
    conn.close()


def get_report(report_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def get_all_reports() -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reports ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_reports_by_severity(severity: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reports WHERE severity = ? ORDER BY created_at DESC",
        (severity,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_reports_by_status(status: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reports WHERE status = ? ORDER BY created_at DESC",
        (status,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_report_status(report_id: int, status: str):
    conn = get_connection()
    conn.execute(
        "UPDATE reports SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, report_id)
    )
    conn.commit()
    conn.close()


def get_stats() -> dict:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    critical = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE severity = 'Critical'"
    ).fetchone()[0]
    high = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE severity = 'High'"
    ).fetchone()[0]
    medium = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE severity = 'Medium'"
    ).fetchone()[0]
    low = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE severity = 'Low'"
    ).fetchone()[0]
    open_reports = conn.execute(
        "SELECT COUNT(*) FROM reports WHERE status = 'Open'"
    ).fetchone()[0]
    conn.close()
    return {
        "total": total,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "open": open_reports,
    }


def search_reports(query: str) -> list:
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM reports
        WHERE title LIKE ? OR description LIKE ? OR category LIKE ?
        ORDER BY created_at DESC
    """, (f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    conn.close()
    return [dict(row) for row in rows]


init_db()
