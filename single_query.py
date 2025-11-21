"""
Single Query Runner with Automatic Logging
Perfect for testing and generating trace logs for assignment
"""

import sys
import os
from datetime import datetime
from agent import SQLDatabaseAgent

def main():
    # Configuration
    API_KEY = "GEMINI_API_KEY"
    DB_PATH = "sample.db"
    
    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        # Create descriptive log filename from query
        query_slug = query[:30].replace(" ", "_").replace("?", "")
        log_filename = f"trace_{query_slug}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    else:
        query = "How many customers are in the database?"
        log_filename = f"trace_default_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    print("="*70)
    print("SQL DATABASE AGENT - SINGLE QUERY WITH LOGGING".center(70))
    print("="*70)
    print(f"\nQuery: {query}")
    print(f"Log file: {log_filename}")
    print("-"*70)
    print()
    
    # Initialize agent with logging
    agent = SQLDatabaseAgent(
        api_key=API_KEY,
        db_path=DB_PATH,
        use_stable_model=True,
        enable_logging=True,
        log_filename=log_filename
    )
    
    try:
        # Run the query
        result = agent.run(query)
        
        print("\n" + "="*70)
        print("FINAL RESULT:")
        print("="*70)
        print(result)
        print()
        
        print("="*70)
        print(f"✓ Complete trace saved to: {log_filename}")
        print(f"✓ File size: {os.path.getsize(log_filename)} bytes")
        print("="*70)
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        
        if "rate limit" in str(e).lower() or "quota" in str(e).lower():
            print("\n⚠️  RATE LIMIT TROUBLESHOOTING:")
            print("="*70)
            print("1. Wait 60 seconds before trying again")
            print("2. Check your quota: https://ai.dev/usage?tab=rate-limit")
            print("3. The agent is already using gemini-2.5-flash for better limits")
    
    finally:
        agent.close()


def generate_assignment_traces():
    """Generate the 3 trace logs required for assignment submission"""
    API_KEY = "GEMINI_API_KEY"
    DB_PATH = "sample.db"
    
    # Create traces directory
    os.makedirs("trace_logs", exist_ok=True)
    
    # Define the 3 example queries for assignment
    examples = [
        ("Schema Discovery", "What tables are in this database?", "trace_schema_discovery.txt"),
        ("Aggregation Query", "What is the total amount of all orders?", "trace_aggregation.txt"),
        ("Error Recovery", "How many employees are there?", "trace_error_recovery.txt")
    ]
    
    print("="*70)
    print("GENERATING ASSIGNMENT TRACE LOGS".center(70))
    print("="*70)
    print("\nThis will create 3 trace logs for your assignment submission:")
    print("1. trace_logs/trace_schema_discovery.txt")
    print("2. trace_logs/trace_aggregation.txt")
    print("3. trace_logs/trace_error_recovery.txt")
    print("\nEstimated time: 2-3 minutes with rate limit delays")
    print("="*70)
    print()
    
    for i, (name, query, filename) in enumerate(examples, 1):
        log_path = os.path.join("trace_logs", filename)
        
        print(f"\n[{i}/3] Generating: {name}")
        print(f"Query: {query}")
        print(f"Output: {log_path}")
        print("-"*70)
        
        agent = SQLDatabaseAgent(
            api_key=API_KEY,
            db_path=DB_PATH,
            use_stable_model=True,
            enable_logging=True,
            log_filename=log_path
        )
        
        try:
            result = agent.run(query)
            print(f"✓ Generated {filename}")
            agent.close()
            
            # Wait between queries to avoid rate limits
            if i < len(examples):
                import time
                print("\n[Waiting 10s before next query...]")
                time.sleep(10)
                
        except Exception as e:
            print(f"✗ Error generating {filename}: {str(e)}")
            agent.close()
            
            if "rate limit" in str(e).lower():
                print("\n⚠️  Rate limit hit. Please wait 60 seconds and run again.")
                break
    
    print("\n" + "="*70)
    print("TRACE GENERATION COMPLETE")
    print("="*70)
    print("\nGenerated files in trace_logs/ directory:")
    print("- These files contain full THOUGHT/ACTION/OBSERVATION traces")
    print("- Include these in your assignment submission")
    print("- They demonstrate the ReAct loop in action")
    print()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║     SQL Database Agent - Query Runner with Logging         ║
╚════════════════════════════════════════════════════════════╝

USAGE:

1. Run with custom query:
   python run_with_log.py "Your query here"
   
2. Run with default query:
   python run_with_log.py
   
3. Generate assignment trace logs:
   python run_with_log.py --generate-traces

Each run creates a timestamped log file with the complete trace.
""")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--generate-traces":
        generate_assignment_traces()
    else:
        main()