"""
View Database Contents - Shows all tables and data
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("data/scholarai.db")

def view_database():
    if not DB_PATH.exists():
        print(f"❌ Database not found at: {DB_PATH}")
        return
    
    print(f"\n{'='*70}")
    print(f"SCHOLARAI DATABASE VIEWER")
    print(f"{'='*70}")
    print(f"Location: {DB_PATH.absolute()}")
    print(f"Size: {DB_PATH.stat().st_size:,} bytes")
    print(f"{'='*70}\n")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 TABLES: {len(tables)}")
    print(f"   {', '.join(tables)}\n")
    
    # Show each table
    for table in tables:
        print(f"\n{'─'*70}")
        print(f"📋 TABLE: {table}")
        print(f"{'─'*70}")
        
        # Get schema
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print(f"\n🔧 COLUMNS ({len(columns)}):")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            is_pk = " (PRIMARY KEY)" if col[5] else ""
            not_null = " NOT NULL" if col[3] else ""
            print(f"   • {col_name:<20} {col_type:<10} {is_pk}{not_null}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        print(f"\n📊 ROWS: {count}")
        
        if count > 0:
            # Show sample data
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
            
            print(f"\n📝 SAMPLE DATA (showing up to 5 rows):")
            for i, row in enumerate(rows, 1):
                print(f"\n   Row {i}:")
                for key in row.keys():
                    value = row[key]
                    # Mask sensitive data
                    if key in ['password_hash', 'reset_token', 'remember_token']:
                        value = '*' * 20 if value else None
                    elif key == 'verification_code' and value:
                        value = f"{value[:2]}****"
                    # Truncate long text
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:47] + "..."
                    print(f"      {key:<20} = {value}")
    
    conn.close()
    
    print(f"\n{'='*70}")
    print(f"DATABASE SUMMARY")
    print(f"{'='*70}")
    
    # Reopen for summary stats
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # User stats
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_verified = 1")
    verified_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE tier = 'premium'")
    premium_users = cursor.fetchone()[0]
    
    # Review stats
    cursor.execute("SELECT COUNT(*) FROM reviews")
    total_reviews = cursor.fetchone()[0]
    
    cursor.execute("SELECT AVG(word_count) FROM reviews")
    avg_words = cursor.fetchone()[0] or 0
    
    # Session stats
    cursor.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cursor.fetchone()[0]
    
    print(f"\n👥 USERS:")
    print(f"   Total: {total_users}")
    print(f"   Verified: {verified_users}")
    print(f"   Unverified: {total_users - verified_users}")
    print(f"   Premium: {premium_users}")
    print(f"   Free: {total_users - premium_users}")
    
    print(f"\n📚 REVIEWS:")
    print(f"   Total: {total_reviews}")
    print(f"   Avg Words: {int(avg_words)}")
    
    print(f"\n🔗 SESSIONS:")
    print(f"   Total: {total_sessions}")
    
    conn.close()
    
    print(f"\n{'='*70}\n")

if __name__ == "__main__":
    view_database()
