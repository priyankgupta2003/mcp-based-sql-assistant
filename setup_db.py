import sqlite3
from datetime import datetime

def setup_database():
    """Create and populate the SQLite database with sample data."""
    # Connect to SQLite database (creates file if it doesn't exist)
    conn = sqlite3.connect('sales.db')
    cursor = conn.cursor()
    
    # Drop tables if they exist (for clean setup)
    cursor.execute('DROP TABLE IF EXISTS sales')
    cursor.execute('DROP TABLE IF EXISTS products')
    
    # Create products table
    cursor.execute('''
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL
        )
    ''')
    
    # Create sales table
    cursor.execute('''
        CREATE TABLE sales (
            sale_id INTEGER PRIMARY KEY,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            region TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (product_id)
        )
    ''')
    
    # Insert sample products
    products_data = [
        (1, 'Laptop', 'Electronics', 999.99),
        (2, 'Mouse', 'Electronics', 29.99),
        (3, 'Keyboard', 'Electronics', 79.99),
        (4, 'Monitor', 'Electronics', 299.99),
        (5, 'Office Chair', 'Furniture', 199.99),
        (6, 'Desk', 'Furniture', 349.99),
        (7, 'Notebook', 'Stationery', 4.99)
    ]
    
    cursor.executemany('''
        INSERT INTO products (product_id, name, category, price)
        VALUES (?, ?, ?, ?)
    ''', products_data)
    
    # Insert sample sales
    sales_data = [
        (1, 1, 2, '2023-10-15', 'North'),
        (2, 2, 5, '2023-10-16', 'South'),
        (3, 3, 3, '2023-10-17', 'East'),
        (4, 1, 1, '2023-10-18', 'West'),
        (5, 4, 2, '2023-10-19', 'North'),
        (6, 5, 1, '2023-10-20', 'South'),
        (7, 6, 1, '2023-10-21', 'East'),
        (8, 7, 10, '2023-10-22', 'West'),
        (9, 2, 3, '2023-10-23', 'North'),
        (10, 3, 2, '2023-10-24', 'South'),
        (11, 1, 1, '2023-11-01', 'East'),
        (12, 4, 3, '2023-11-02', 'West')
    ]
    
    cursor.executemany('''
        INSERT INTO sales (sale_id, product_id, quantity, sale_date, region)
        VALUES (?, ?, ?, ?, ?)
    ''', sales_data)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Database setup complete! Created sales.db with sample data.")
    print("Tables created: products, sales")
    print(f"Inserted {len(products_data)} products and {len(sales_data)} sales records.")

if __name__ == "__main__":
    setup_database()
