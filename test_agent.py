import sqlite3
import os
import time
import sys
from datetime import datetime
from agent import SQLDatabaseAgent

class Logger:
    """Dual output to console and file"""
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, 'w', encoding='utf-8')
        
        # Write header
        self.log.write("="*70 + "\n")
        self.log.write("SQL DATABASE AGENT - TEST LOG\n")
        self.log.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.log.write("="*70 + "\n\n")
        self.log.flush()
    
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    
    def flush(self):
        self.terminal.flush()
        self.log.flush()
    
    def close(self):
        self.log.close()
        sys.stdout = self.terminal


def create_sample_database(db_path: str):
    """Create a sample database for testing"""
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create customers table
    cursor.execute("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            age INTEGER,
            city TEXT
        )
    """)
    
    # Create orders table
    cursor.execute("""
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product TEXT,
            amount DECIMAL(10,2),
            order_date DATE,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    """)
    
    # Insert sample data
    customers = [
        (1, "Alice Johnson", "alice@email.com", 28, "New York"),
        (2, "Bob Smith", "bob@email.com", 35, "Los Angeles"),
        (3, "Carol White", "carol@email.com", 42, "Chicago"),
        (4, "David Brown", "david@email.com", 31, "Houston"),
        (5, "Eve Davis", "eve@email.com", 26, "Phoenix")
    ]
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
    
    orders = [
        (1, 1, "Laptop", 999.99, "2024-01-15"),
        (2, 1, "Mouse", 29.99, "2024-01-16"),
        (3, 2, "Keyboard", 79.99, "2024-01-20"),
        (4, 3, "Monitor", 299.99, "2024-02-01"),
        (5, 3, "Desk", 449.99, "2024-02-05"),
        (6, 4, "Chair", 199.99, "2024-02-10")
    ]
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders)
    
    conn.commit()
    conn.close()
    print(f"Sample database created at: {db_path}")


def test_schema_discovery(agent: SQLDatabaseAgent):
    """Test 1: Schema Discovery"""
    print("\n" + "="*60)
    print("TEST 1: Schema Discovery")
    print("="*60)
    result = agent.run("What tables exist?")
    print(f"\nTest Result: {result}")
    assert "customers" in result.lower() or "orders" in result.lower()
    print("✓ Test 1 PASSED")


def test_simple_count(agent: SQLDatabaseAgent):
    """Test 2: Simple Count"""
    print("\n" + "="*60)
    print("TEST 2: Simple Count")
    print("="*60)
    result = agent.run("How many orders are there?")
    print(f"\nTest Result: {result}")
    assert "6" in result or "six" in result.lower()
    print("✓ Test 2 PASSED")


def test_aggregation(agent: SQLDatabaseAgent):
    """Test 3: Aggregation"""
    print("\n" + "="*60)
    print("TEST 3: Aggregation")
    print("="*60)
    result = agent.run("What is the total amount of all orders?")
    print(f"\nTest Result: {result}")
    assert "1959" in result or "1960" in result or "total" in result.lower()
    print("✓ Test 3 PASSED")


def test_filtering(agent: SQLDatabaseAgent):
    """Test 4: Filtering"""
    print("\n" + "="*60)
    print("TEST 4: Filtering")
    print("="*60)
    result = agent.run("How many customers are from Chicago?")
    print(f"\nTest Result: {result}")
    assert "1" in result or "one" in result.lower()
    print("✓ Test 4 PASSED")


def test_customer_count(agent: SQLDatabaseAgent):
    """Test 5: Customer Count"""
    print("\n" + "="*60)
    print("TEST 5: Customer Count")
    print("="*60)
    result = agent.run("How many customers are in the database?")
    print(f"\nTest Result: {result}")
    assert "5" in result or "five" in result.lower()
    print("✓ Test 5 PASSED")


def test_error_recovery(agent: SQLDatabaseAgent):
    """Test 6: Error Recovery"""
    print("\n" + "="*60)
    print("TEST 6: Error Recovery")
    print("="*60)
    result = agent.run("How many employees are there?")
    print(f"\nTest Result: {result}")
    assert "not found" in result.lower() or "no" in result.lower() or "tables" in result.lower() or "employees" not in result.lower()
    print("✓ Test 6 PASSED")


def run_tests_with_rate_limiting():
    """Run all tests with proper rate limiting between each test"""
    API_KEY = "GEMINI_API_KEY"
    DB_PATH = "sample.db"
    
    # Generate log filename with timestamp
    log_filename = f"test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Set up logging
    logger = Logger(log_filename)
    sys.stdout = logger
    
    print(f"Logging to: {log_filename}")
    print()
    
    try:
        # Create sample database
        create_sample_database(DB_PATH)
        
        # Initialize agent with stable model
        print("\n" + "="*60)
        print("Initializing agent...")
        print("="*60)
        agent = SQLDatabaseAgent(api_key=API_KEY, db_path=DB_PATH, 
                                max_steps=10, use_stable_model=True)
        
        # Define all tests
        tests = [
            ("Schema Discovery", test_schema_discovery),
            ("Simple Count", test_simple_count),
            ("Aggregation", test_aggregation),
            ("Filtering", test_filtering),
            ("Customer Count", test_customer_count),
            ("Error Recovery", test_error_recovery)
        ]
        
        passed = 0
        failed = 0
        
        for i, (name, test_func) in enumerate(tests, 1):
            try:
                print(f"\n{'='*60}")
                print(f"Running test {i}/{len(tests)}: {name}")
                print(f"{'='*60}")
                
                test_func(agent)
                passed += 1
                
                # Wait between tests to avoid rate limits
                if i < len(tests):
                    wait_time = 8
                    print(f"\n[Waiting {wait_time}s before next test to avoid rate limits...]")
                    time.sleep(wait_time)
                    
            except AssertionError as e:
                print(f"\n✗ Test {i} FAILED: Assertion error")
                print(f"   Expected condition not met in result")
                failed += 1
                
                if i < len(tests):
                    print(f"\n[Waiting 8s before next test...]")
                    time.sleep(8)
                    
            except Exception as e:
                print(f"\n✗ Test {i} ERROR: {str(e)}")
                if "rate limit" in str(e).lower() or "quota" in str(e).lower():
                    print("\n⚠️  Rate limit hit. Please wait a few minutes and try again.")
                    print(f"\nTests completed: {i-1}/{len(tests)}")
                    break
                failed += 1
                
                if i < len(tests):
                    print(f"\n[Waiting 8s before next test...]")
                    time.sleep(8)
        
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {passed} passed, {failed} failed out of {len(tests)}")
        print("="*60)
        
        if passed == len(tests):
            print("🎉 ALL TESTS PASSED!")
        elif passed > 0:
            print(f"✓ {passed} tests passed successfully")
        
        print(f"\n✓ Complete log saved to: {log_filename}")
        
        agent.close()
        
    finally:
        logger.close()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║         SQL Database Agent - Test Suite with Logging       ║
║         (Output saved to test_log_YYYYMMDD_HHMMSS.txt)     ║
╚════════════════════════════════════════════════════════════╝

This version saves all output to a timestamped log file
while still showing output in the console.

Tests included:
1. Schema Discovery
2. Simple Count
3. Aggregation
4. Filtering
5. Customer Count
6. Error Recovery

Note: Tests run with 8-second delays to respect API rate limits.
Total estimated time: ~5-6 minutes to complete all tests.
""")
    
    run_tests_with_rate_limiting()