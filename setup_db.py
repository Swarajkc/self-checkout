import sqlite3

def setup_database():
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            item_name TEXT PRIMARY KEY,
            quantity INTEGER
        )
    ''')
    conn.commit()
    conn.close()
    print("Database setup completed!")

if __name__ == "__main__":
    setup_database()
