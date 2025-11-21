import sqlite3
import json
import re
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import google.generativeai as genai

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(log_filename=None):
    """Set up logging to both file and console"""
    if log_filename is None:
        log_filename = f"agent_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    # Create logger
    logger = logging.getLogger('SQLAgent')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_format)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging to: {log_filename}")
    return logger, log_filename


# ============================================================================
# TOOL SYSTEM
# ============================================================================

class Tool:
    """Base tool interface"""
    def __init__(self, name: str, description: str, parameters: Dict[str, str]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    def call(self, **kwargs) -> str:
        raise NotImplementedError
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class ListTablesTool(Tool):
    def __init__(self, db_connection):
        super().__init__(
            name="list_tables",
            description="Lists all tables in the database",
            parameters={}
        )
        self.db = db_connection
    
    def call(self, **kwargs) -> str:
        cursor = self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]
        return f"Available tables: {', '.join(tables)}" if tables else "No tables found"


class DescribeTableTool(Tool):
    def __init__(self, db_connection):
        super().__init__(
            name="describe_table",
            description="Describes the schema of a table (columns, types, row count)",
            parameters={"table_name": "Name of the table to describe (string)"}
        )
        self.db = db_connection
    
    def call(self, table_name: str, **kwargs) -> str:
        try:
            cursor = self.db.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            if not columns:
                return f"Table '{table_name}' not found"
            
            schema = f"Table: {table_name}\nColumns:\n"
            for col in columns:
                schema += f"  - {col[1]} ({col[2]})\n"
            
            count_cursor = self.db.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = count_cursor.fetchone()[0]
            schema += f"Row count: {row_count}"
            return schema
        except sqlite3.Error as e:
            return f"Error describing table: {str(e)}"


class QueryDatabaseTool(Tool):
    def __init__(self, db_connection):
        super().__init__(
            name="query_database",
            description="Executes a SELECT query (read-only, max 100 rows)",
            parameters={"query": "SQL SELECT query to execute (string)"}
        )
        self.db = db_connection
    
    def call(self, query: str, **kwargs) -> str:
        if not self._is_safe_query(query):
            return "Error: Only SELECT queries are allowed (read-only mode)"
        
        try:
            query = self._add_limit(query)
            cursor = self.db.execute(query)
            rows = cursor.fetchall()
            
            if not rows:
                return "Query executed successfully. No rows returned."
            
            columns = [desc[0] for desc in cursor.description]
            result = self._format_results(columns, rows)
            return result
        except sqlite3.Error as e:
            return f"SQL Error: {str(e)}. Check your query syntax."
    
    def _is_safe_query(self, query: str) -> bool:
        query_upper = query.upper().strip()
        dangerous = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 'REPLACE']
        return query_upper.startswith('SELECT') and not any(d in query_upper for d in dangerous)
    
    def _add_limit(self, query: str) -> str:
        if 'LIMIT' not in query.upper():
            query = query.rstrip(';') + ' LIMIT 100'
        return query
    
    def _format_results(self, columns: List[str], rows: List[tuple]) -> str:
        result = f"Columns: {', '.join(columns)}\n"
        result += f"Returned {len(rows)} row(s):\n"
        for i, row in enumerate(rows[:10], 1):
            result += f"  {i}. {row}\n"
        if len(rows) > 10:
            result += f"  ... and {len(rows) - 10} more rows\n"
        return result


# ============================================================================
# CORE AGENT CLASS WITH LOGGING
# ============================================================================

class SQLDatabaseAgent:
    def __init__(self, api_key: str, db_path: str, max_steps: int = 10, 
                 use_stable_model: bool = True, enable_logging: bool = True,
                 log_filename: str = None):
        genai.configure(api_key=api_key)
        
        # Set up logging
        if enable_logging:
            self.logger, self.log_filename = setup_logging(log_filename)
        else:
            self.logger = None
            self.log_filename = None
        
        model_name = 'gemini-2.5-flash' if use_stable_model else 'gemini-2.0-flash-exp'
        self.model = genai.GenerativeModel(model_name)
        self._log(f"Using model: {model_name}", level='info')
        
        self.db = sqlite3.connect(db_path)
        self.max_steps = max_steps
        self.tools = self._init_tools()
        self.conversation_history = []
        self.request_delay = 2.0
        self.last_request_time = 0
        self.max_retries = 3
    
    def _log(self, message: str, level='info'):
        """Log message if logging is enabled"""
        if self.logger:
            if level == 'debug':
                self.logger.debug(message)
            elif level == 'warning':
                self.logger.warning(message)
            elif level == 'error':
                self.logger.error(message)
            else:
                self.logger.info(message)
        else:
            print(message)
    
    def _init_tools(self) -> Dict[str, Tool]:
        return {
            "list_tables": ListTablesTool(self.db),
            "describe_table": DescribeTableTool(self.db),
            "query_database": QueryDatabaseTool(self.db)
        }
    
    def _build_system_prompt(self) -> str:
        tools_desc = "\n".join([
            f"- {tool.name}({', '.join(tool.parameters.keys()) if tool.parameters else 'no parameters'}): {tool.description}"
            for tool in self.tools.values()
        ])
        
        return f"""You are a SQL database agent. Follow the ReAct pattern strictly.

AVAILABLE TOOLS:
{tools_desc}

OUTPUT FORMAT (use exactly this structure):
THOUGHT: [your reasoning about what to do next]
ACTION: tool_name{{"param": "value"}}

After receiving an OBSERVATION, continue with another THOUGHT-ACTION cycle or provide:
FINAL ANSWER: [concise answer to the user's question]

RULES:
1. Always start with THOUGHT
2. Use ACTION with valid JSON parameters
3. Explore schema before querying (list_tables, describe_table)
4. Only use SELECT queries
5. Provide FINAL ANSWER when you have the complete answer

EXAMPLE:
User: How many users are there?
THOUGHT: I need to find tables first
ACTION: list_tables{{}}
[After observation]
THOUGHT: Found users table, let me check its schema
ACTION: describe_table{{"table_name": "users"}}
[After observation]
THOUGHT: Now I can count the rows
ACTION: query_database{{"query": "SELECT COUNT(*) FROM users"}}
[After observation]
FINAL ANSWER: There are 150 users in the database."""
    
    def _parse_llm_response(self, response: str) -> tuple[Optional[str], Optional[str], Optional[Dict]]:
        thought_match = re.search(r'THOUGHT:\s*(.+?)(?=ACTION:|FINAL ANSWER:|$)', response, re.DOTALL | re.IGNORECASE)
        action_match = re.search(r'ACTION:\s*(\w+)\s*({.*?})', response, re.DOTALL | re.IGNORECASE)
        final_match = re.search(r'FINAL ANSWER:\s*(.+)', response, re.DOTALL | re.IGNORECASE)
        
        thought = thought_match.group(1).strip() if thought_match else None
        
        if final_match:
            return thought, "FINAL_ANSWER", {"answer": final_match.group(1).strip()}
        
        if action_match:
            tool_name = action_match.group(1).strip()
            try:
                params = json.loads(action_match.group(2))
                return thought, tool_name, params
            except json.JSONDecodeError:
                return thought, None, None
        
        return thought, None, None
    
    def _execute_tool(self, tool_name: str, params: Dict) -> str:
        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"
        return self.tools[tool_name].call(**params)
    
    def _call_llm_with_retry(self, prompt: str) -> str:
        """Call LLM with exponential backoff retry logic"""
        for attempt in range(self.max_retries):
            try:
                time_since_last = time.time() - self.last_request_time
                if time_since_last < self.request_delay:
                    sleep_time = self.request_delay - time_since_last
                    self._log(f"[Rate limit] Waiting {sleep_time:.1f}s before next request...")
                    time.sleep(sleep_time)
                
                response = self.model.generate_content(prompt)
                self.last_request_time = time.time()
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                
                if "429" in error_msg or "quota" in error_msg.lower():
                    retry_match = re.search(r'retry in (\d+\.?\d*)', error_msg)
                    if retry_match:
                        retry_delay = float(retry_match.group(1))
                    else:
                        retry_delay = (2 ** attempt) * 10
                    
                    self._log(f"[Rate limit hit] Waiting {retry_delay:.1f}s before retry {attempt + 1}/{self.max_retries}...", level='warning')
                    time.sleep(retry_delay)
                    
                    if attempt == self.max_retries - 1:
                        raise Exception(f"Rate limit exceeded after {self.max_retries} retries. Please wait and try again.")
                else:
                    raise e
        
        raise Exception("Failed to call LLM after maximum retries")
    
    def run(self, query: str) -> str:
        self._log(f"\n{'='*60}")
        self._log(f"NEW QUERY: {query}")
        self._log(f"{'='*60}")
        
        system_prompt = self._build_system_prompt()
        self.conversation_history = [f"User Query: {query}"]
        
        full_context = f"{system_prompt}\n\n{query}"
        
        for step in range(self.max_steps):
            try:
                context = full_context + "\n" + "\n".join(self.conversation_history[-6:])
                llm_output = self._call_llm_with_retry(context)
                
                thought, action, params = self._parse_llm_response(llm_output)
                
                if thought:
                    log_entry = f"\nSTEP {step + 1}\nTHOUGHT: {thought}"
                    self.conversation_history.append(log_entry)
                    self._log(log_entry)
                
                if action == "FINAL_ANSWER":
                    final = f"FINAL ANSWER: {params['answer']}"
                    self.conversation_history.append(final)
                    self._log(f"\n{final}")
                    return params['answer']
                
                if action and params is not None:
                    action_log = f"ACTION: {action}{json.dumps(params)}"
                    self.conversation_history.append(action_log)
                    self._log(action_log)
                    
                    observation = self._execute_tool(action, params)
                    obs_log = f"OBSERVATION: {observation}"
                    self.conversation_history.append(obs_log)
                    self._log(obs_log)
                else:
                    error_msg = "Error: Could not parse action. Please use format: ACTION: tool_name{\"param\": \"value\"}"
                    self.conversation_history.append(error_msg)
                    self._log(error_msg, level='warning')
                
            except Exception as e:
                error = f"Error in step {step + 1}: {str(e)}"
                self._log(error, level='error')
                self.conversation_history.append(error)
                
                if "rate limit" in error.lower() or "quota" in error.lower():
                    self._log("Stopping execution due to rate limits.", level='error')
                    break
        
        final = "FINAL ANSWER: Maximum steps reached. Could not complete the query fully."
        self._log(f"\n{final}")
        return final
    
    def close(self):
        self.db.close()
        if self.log_filename:
            self._log(f"\n{'='*60}")
            self._log(f"Session ended. Log saved to: {self.log_filename}")
            self._log(f"{'='*60}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    API_KEY = "GEMINI_API_KEY"
    DB_PATH = "sample.db"
    
    # Initialize with logging enabled
    agent = SQLDatabaseAgent(
        api_key=API_KEY, 
        db_path=DB_PATH, 
        use_stable_model=True,
        enable_logging=True  # Set to False to disable logging
    )
    
    try:
        # Run multiple queries - all will be logged
        queries = [
            "How many customers are in the database?",
            "What is the total amount of all orders?"
        ]
        
        for query in queries:
            result = agent.run(query)
            print(f"\nResult: {result}\n")
            time.sleep(5)  # Wait between queries
            
    finally:
        agent.close()