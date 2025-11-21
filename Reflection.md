# Reflection: SQL Database Agent

## Design Trade-offs

**Simplicity vs. Power**: I chose to build a minimal ReAct agent (~330 lines) without external frameworks, prioritizing code clarity and educational value over advanced features. This makes the codebase easy to understand but limits extensibility compared to production frameworks like LangChain.

**Safety vs. Flexibility**: The agent only allows `SELECT` queries and automatically adds `LIMIT 100` clauses. While this prevents data mutations and runaway queries, it restricts legitimate use cases like analyzing large datasets or performing database maintenance.

**Cost vs. Performance**: Using Gemini 2.5 Flash (gemini-1.5-flash) keeps costs near zero with generous rate limits (15 RPM free tier) and strong reasoning capabilities. While more advanced models exist, Gemini 2.5 Flash provides an excellent balance of speed, accuracy, and affordability for database query tasks.

## Failure Modes

**Hallucinated Table Names**: The agent sometimes attempts to query non-existent tables despite having the schema. This occurs when the LLM "remembers" common table names from training data rather than consulting the actual database schema.

**Infinite Tool Loops**: Without the 10-step limit, the agent can get stuck repeating the same failing query. The max-steps guard is essential but arbitrary—some complex queries legitimately need more steps.

**Ambiguous Queries**: Natural language like "recent orders" fails without temporal context. The agent cannot infer business logic (e.g., "recent" = last 30 days) and requires explicit date columns.

**Rate Limit Fragility**: Free-tier API limits make the test suite unreliable. A single rate limit error can cascade through multiple tests, requiring manual intervention and wait times between query batches.

## Future Directions

1. **Query Validation**: Add a pre-execution validator that checks if referenced tables/columns exist before running SQL
2. **Memory System**: Implement conversation memory to avoid re-discovering schemas in multi-turn interactions
3. **Streaming Output**: Add real-time token streaming for better user experience with long-running queries
4. **Multi-Database Support**: Extend beyond SQLite to PostgreSQL, MySQL, and cloud databases
5. **Semantic Caching**: Cache embeddings of similar queries to reduce API calls and improve response time
6. **Error Recovery**: Implement automatic query refinement when syntax errors occur, using error messages as feedback
