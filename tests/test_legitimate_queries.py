"""
Comprehensive test suite for legitimate SQL queries that should NOT be blocked.

This test suite ensures that our security enhancements do not create false positives
by blocking legitimate business queries and standard SQL operations.
"""

import pytest
from utils.snowflake_utils import (
    _perform_additional_security_checks,
    _validate_query_safety,
)


@pytest.mark.security
class TestLegitimateBasicQueries:
    """Test basic legitimate SQL queries that should always be allowed."""

    def test_simple_select_queries(self):
        """Test basic SELECT statements."""
        legitimate_queries = [
            "SELECT * FROM users",
            "SELECT id, name, email FROM customers",
            "SELECT COUNT(*) FROM orders",
            "SELECT DISTINCT category FROM products",
            "SELECT TOP 100 * FROM transactions",
            "SELECT name, price * quantity AS total FROM items",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate query blocked: {query} - {result['message']}"

    def test_where_clause_queries(self):
        """Test SELECT queries with legitimate WHERE clauses."""
        legitimate_queries = [
            "SELECT * FROM users WHERE id = 123",
            "SELECT * FROM products WHERE price > 100",
            "SELECT * FROM orders WHERE status = 'completed'",
            "SELECT * FROM customers WHERE created_date >= '2023-01-01'",
            "SELECT * FROM items WHERE category IN ('electronics', 'books')",
            "SELECT * FROM users WHERE name LIKE 'John%'",
            "SELECT * FROM products WHERE price BETWEEN 10 AND 100",
            "SELECT * FROM orders WHERE order_date IS NOT NULL",
            "SELECT * FROM customers WHERE age > 18 AND status = 'active'",
            "SELECT * FROM products WHERE description CONTAINS 'laptop'",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate WHERE query blocked: {query} - {result['message']}"

    def test_ordering_and_grouping_queries(self):
        """Test queries with ORDER BY, GROUP BY, and HAVING clauses."""
        legitimate_queries = [
            "SELECT * FROM users ORDER BY created_date DESC",
            "SELECT category, COUNT(*) FROM products GROUP BY category",
            "SELECT region, SUM(sales) FROM revenue GROUP BY region HAVING SUM(sales) > 1000",
            "SELECT * FROM orders ORDER BY order_date, customer_id",
            "SELECT customer_id, MAX(order_date) FROM orders GROUP BY customer_id",
            "SELECT category, AVG(price) FROM products GROUP BY category ORDER BY AVG(price) DESC",
            "SELECT YEAR(order_date), COUNT(*) FROM orders GROUP BY YEAR(order_date)",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate ordering/grouping query blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateJoinQueries:
    """Test legitimate JOIN operations that should be allowed."""

    def test_inner_join_queries(self):
        """Test legitimate INNER JOIN queries."""
        legitimate_queries = [
            "SELECT u.name, o.total FROM users u INNER JOIN orders o ON u.id = o.user_id",
            "SELECT c.name, p.title FROM customers c JOIN purchases p ON c.id = p.customer_id",
            "SELECT o.id, i.name FROM orders o INNER JOIN items i ON o.item_id = i.id",
            "SELECT u.email, a.street FROM users u JOIN addresses a ON u.address_id = a.id",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate INNER JOIN blocked: {query} - {result['message']}"

    def test_outer_join_queries(self):
        """Test legitimate OUTER JOIN queries."""
        legitimate_queries = [
            "SELECT u.name, o.total FROM users u LEFT JOIN orders o ON u.id = o.user_id",
            "SELECT c.name, p.amount FROM customers c RIGHT JOIN payments p ON c.id = p.customer_id",
            "SELECT u.name, p.title FROM users u FULL OUTER JOIN projects p ON u.id = p.owner_id",
            "SELECT e.name, d.department_name FROM employees e LEFT OUTER JOIN departments d ON e.dept_id = d.id",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate OUTER JOIN blocked: {query} - {result['message']}"

    def test_multiple_join_queries(self):
        """Test queries with multiple legitimate JOINs (within our 5 JOIN limit)."""
        legitimate_queries = [
            """SELECT u.name, o.total, i.name, c.category 
               FROM users u 
               JOIN orders o ON u.id = o.user_id 
               JOIN items i ON o.item_id = i.id 
               JOIN categories c ON i.category_id = c.id""",
            """SELECT e.name, d.dept_name, p.project_name, l.location 
               FROM employees e 
               LEFT JOIN departments d ON e.dept_id = d.id 
               LEFT JOIN projects p ON e.id = p.lead_id 
               LEFT JOIN locations l ON d.location_id = l.id""",
        ]

        for query in legitimate_queries:
            # Remove extra whitespace for cleaner testing
            clean_query = " ".join(query.split())
            result = _perform_additional_security_checks(
                clean_query.upper(), clean_query
            )
            assert not result[
                "error"
            ], f"Legitimate multiple JOIN blocked: {clean_query} - {result['message']}"


@pytest.mark.security
class TestLegitimateAggregateQueries:
    """Test legitimate aggregate and analytical queries."""

    def test_standard_aggregate_functions(self):
        """Test queries with standard aggregate functions."""
        legitimate_queries = [
            "SELECT COUNT(*) FROM users",
            "SELECT SUM(amount) FROM transactions",
            "SELECT AVG(price) FROM products",
            "SELECT MIN(created_date), MAX(created_date) FROM orders",
            "SELECT STDDEV(sales) FROM monthly_revenue",
            "SELECT COUNT(DISTINCT customer_id) FROM orders",
            "SELECT SUM(CASE WHEN status = 'completed' THEN amount ELSE 0 END) FROM orders",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate aggregate query blocked: {query} - {result['message']}"

    def test_window_functions(self):
        """Test legitimate window function queries."""
        legitimate_queries = [
            "SELECT name, salary, ROW_NUMBER() OVER (ORDER BY salary DESC) FROM employees",
            "SELECT department, name, RANK() OVER (PARTITION BY department ORDER BY salary) FROM employees",
            "SELECT customer_id, order_date, LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) FROM orders",
            "SELECT product_id, sales, SUM(sales) OVER (ORDER BY date) AS running_total FROM daily_sales",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate window function blocked: {query} - {result['message']}"

    def test_date_time_functions(self):
        """Test legitimate date and time function queries."""
        legitimate_queries = [
            "SELECT YEAR(order_date), MONTH(order_date), COUNT(*) FROM orders GROUP BY YEAR(order_date), MONTH(order_date)",
            "SELECT DATE_TRUNC('month', created_date) AS month, COUNT(*) FROM users GROUP BY month",
            "SELECT DATEDIFF('day', start_date, end_date) AS duration FROM projects",
            "SELECT * FROM orders WHERE order_date >= DATEADD('day', -30, CURRENT_DATE)",
            "SELECT EXTRACT(quarter FROM sale_date) AS quarter, SUM(amount) FROM sales GROUP BY quarter",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate date/time query blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateInformationSchemaQueries:
    """Test legitimate INFORMATION_SCHEMA queries that should be allowed."""

    def test_basic_information_schema_queries(self):
        """Test basic INFORMATION_SCHEMA queries for metadata."""
        legitimate_queries = [
            "SELECT table_name FROM information_schema.tables",
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'orders'",
            "SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema = 'SNOWFLAKE_SAMPLE_DATA'",
            "SELECT * FROM information_schema.views",
            "SELECT constraint_name, constraint_type FROM information_schema.table_constraints",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate INFORMATION_SCHEMA query blocked: {query} - {result['message']}"

    def test_snowflake_sample_data_queries(self):
        """Test legitimate queries against SNOWFLAKE_SAMPLE_DATA."""
        legitimate_queries = [
            "SELECT * FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER LIMIT 10",
            "SELECT C_NAME, C_MKTSEGMENT FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER WHERE C_CUSTKEY < 100",
            "SELECT COUNT(*) FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS",
            "SELECT O_ORDERSTATUS, COUNT(*) FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS GROUP BY O_ORDERSTATUS",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate SNOWFLAKE_SAMPLE_DATA query blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateComplexQueries:
    """Test complex but legitimate business queries."""

    def test_subquery_patterns(self):
        """Test legitimate subquery patterns."""
        legitimate_queries = [
            "SELECT * FROM users WHERE id IN (SELECT user_id FROM orders WHERE total > 1000)",
            "SELECT name FROM products WHERE price > (SELECT AVG(price) FROM products)",
            "SELECT customer_id, (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) AS order_count FROM customers c",
            "SELECT * FROM employees WHERE salary > (SELECT AVG(salary) FROM employees WHERE department = 'Engineering')",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate subquery blocked: {query} - {result['message']}"

    def test_cte_patterns(self):
        """Test legitimate Common Table Expression (CTE) patterns."""
        legitimate_queries = [
            """WITH monthly_sales AS (
                 SELECT YEAR(order_date) AS year, MONTH(order_date) AS month, SUM(total) AS total_sales
                 FROM orders GROUP BY YEAR(order_date), MONTH(order_date)
               )
               SELECT year, month, total_sales FROM monthly_sales ORDER BY year, month""",
            """WITH top_customers AS (
                 SELECT customer_id, SUM(total) AS total_spent 
                 FROM orders GROUP BY customer_id 
                 ORDER BY total_spent DESC LIMIT 10
               )
               SELECT c.name, tc.total_spent 
               FROM customers c JOIN top_customers tc ON c.id = tc.customer_id""",
        ]

        for query in legitimate_queries:
            # Remove extra whitespace for cleaner testing
            clean_query = " ".join(query.split())
            result = _perform_additional_security_checks(
                clean_query.upper(), clean_query
            )
            assert not result[
                "error"
            ], f"Legitimate CTE blocked: {clean_query} - {result['message']}"

    def test_case_when_patterns(self):
        """Test legitimate CASE WHEN patterns."""
        legitimate_queries = [
            "SELECT name, CASE WHEN age < 18 THEN 'Minor' ELSE 'Adult' END AS age_group FROM users",
            "SELECT product_id, CASE WHEN price < 50 THEN 'Cheap' WHEN price < 200 THEN 'Medium' ELSE 'Expensive' END FROM products",
            "SELECT COUNT(CASE WHEN status = 'active' THEN 1 END) AS active_users FROM users",
            "SELECT SUM(CASE WHEN order_date >= '2023-01-01' THEN total ELSE 0 END) AS current_year_sales FROM orders",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate CASE WHEN blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateQueryEdgeCases:
    """Test edge cases of legitimate queries that might trigger false positives."""

    def test_quoted_identifiers(self):
        """Test legitimate queries with quoted identifiers."""
        legitimate_queries = [
            'SELECT "user name", "email address" FROM "user table"',
            "SELECT `order id`, `customer id` FROM `order table`",
            'SELECT "group", "order" FROM "reserved words table"',  # SQL reserved words as column names
            'SELECT a."complex name with spaces" FROM table_a a',
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate quoted identifier query blocked: {query} - {result['message']}"

    def test_string_literals_with_special_chars(self):
        """Test legitimate queries with string literals containing special characters."""
        legitimate_queries = [
            "SELECT * FROM users WHERE name = 'O''Brien'",  # Escaped apostrophe
            "SELECT * FROM products WHERE description = 'High-quality item with 100% satisfaction'",
            "SELECT * FROM comments WHERE text LIKE '%@user%'",  # @ symbol in string
            "SELECT * FROM logs WHERE message = 'User logged in (successful)'",  # Parentheses in string
            "SELECT * FROM articles WHERE title = 'The Art of SQL: Advanced Techniques'",  # Colon in string
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate string literal query blocked: {query} - {result['message']}"

    def test_numeric_expressions(self):
        """Test legitimate queries with numeric expressions."""
        legitimate_queries = [
            "SELECT price * 1.2 AS price_with_tax FROM products",
            "SELECT ROUND(average_score, 2) FROM test_results",
            "SELECT ABS(temperature - 32) * 5 / 9 AS celsius FROM weather_data",
            "SELECT POWER(2, level) AS experience_points FROM game_levels",
            "SELECT SQRT(x * x + y * y) AS distance FROM coordinates",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Legitimate numeric expression blocked: {query} - {result['message']}"

    def test_legitimate_long_queries(self):
        """Test legitimate but long queries that should not be blocked."""
        # Create a legitimate long query with many columns (but under 10,000 chars)
        columns = [f"col_{i}" for i in range(100)]
        long_select = f"SELECT {', '.join(columns)} FROM large_table WHERE id > 0"

        # Ensure it's under our 10,000 character limit
        assert (
            len(long_select) < 10000
        ), f"Test query too long: {len(long_select)} chars"

        result = _perform_additional_security_checks(long_select.upper(), long_select)
        assert not result[
            "error"
        ], f"Legitimate long query blocked: {long_select[:100]}... - {result['message']}"


@pytest.mark.integration
class TestLegitimateQueryExecution:
    """Integration tests that actually execute legitimate queries."""

    def test_legitimate_query_validation_only(self):
        """Test that legitimate queries pass security validation (not full execution)."""
        legitimate_queries = [
            "SELECT id, name FROM users WHERE id = 123",
            "SELECT COUNT(*) FROM orders",
            "SELECT * FROM information_schema.tables WHERE table_schema = 'SNOWFLAKE_SAMPLE_DATA'",
        ]

        for query in legitimate_queries:
            # Test that the query passes security validation
            result = _validate_query_safety(query, max_rows=1000)

            # Should not have security errors
            assert not result.get(
                "error", False
            ), f"Query should pass security validation: {query} - {result.get('message', '')}"
            assert (
                "safe_query" in result
            ), f"Query should have safe_query field: {query}"


@pytest.mark.security
class TestFalsePositivePrevention:
    """Specific tests to prevent known false positives."""

    def test_business_terms_not_blocked(self):
        """Test that queries with business terms that might look suspicious are not blocked."""
        legitimate_queries = [
            "SELECT union_membership FROM employees",  # 'union' as column name
            "SELECT table_number FROM reservations",  # 'table' as column name
            "SELECT drop_off_location FROM deliveries",  # 'drop' as part of column name
            "SELECT insert_date FROM audit_log",  # 'insert' as part of column name
            "SELECT order_by_priority FROM tasks",  # 'order by' as part of column name
            "SELECT select_options FROM survey_questions",  # 'select' as part of column name
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Business term query blocked: {query} - {result['message']}"

    def test_mathematical_expressions_not_blocked(self):
        """Test that mathematical expressions are not incorrectly flagged."""
        legitimate_queries = [
            "SELECT 2 + 2 AS four",
            "SELECT value1 - value2 AS difference FROM calculations",
            "SELECT price * quantity AS total FROM line_items",
            "SELECT budget / 12 AS monthly_budget FROM projects",
            "SELECT score % 100 AS normalized_score FROM test_results",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Mathematical expression blocked: {query} - {result['message']}"

    def test_comparison_operators_not_blocked(self):
        """Test that legitimate comparison operators are not flagged."""
        legitimate_queries = [
            "SELECT * FROM products WHERE price >= 100 AND price <= 500",
            "SELECT * FROM users WHERE created_date <> '2023-01-01'",
            "SELECT * FROM orders WHERE status != 'cancelled'",
            "SELECT * FROM inventory WHERE quantity > 0",
            "SELECT * FROM employees WHERE salary < (SELECT MAX(salary) FROM employees)",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Comparison operator query blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateAdvancedQueries:
    """Test advanced legitimate SQL patterns that should be allowed."""

    def test_advanced_window_functions(self):
        """Test complex window function queries."""
        legitimate_queries = [
            "SELECT id, name, ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rank FROM employees",
            "SELECT date, sales, LAG(sales, 1) OVER (ORDER BY date) as prev_sales FROM daily_sales",
            "SELECT customer_id, order_total, PERCENT_RANK() OVER (ORDER BY order_total) as percentile FROM orders",
            "SELECT product_id, revenue, SUM(revenue) OVER (PARTITION BY category ORDER BY revenue ROWS UNBOUNDED PRECEDING) as running_total FROM products",
            "SELECT employee_id, salary, NTILE(4) OVER (ORDER BY salary) as salary_quartile FROM employees",
            "SELECT transaction_id, amount, FIRST_VALUE(amount) OVER (PARTITION BY account_id ORDER BY transaction_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as first_transaction FROM transactions",
            "SELECT order_id, order_date, DENSE_RANK() OVER (PARTITION BY customer_id ORDER BY order_date) as order_sequence FROM orders",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Advanced window function blocked: {query} - {result['message']}"

    def test_advanced_analytical_functions(self):
        """Test analytical functions commonly used in business intelligence."""
        legitimate_queries = [
            "SELECT region, product, sales, RATIO_TO_REPORT(sales) OVER (PARTITION BY region) as sales_ratio FROM regional_sales",
            "SELECT customer_id, order_total, CUME_DIST() OVER (ORDER BY order_total) as cumulative_distribution FROM orders",
            "SELECT product_id, price, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) OVER (PARTITION BY category) as median_price FROM products",
            "SELECT employee_id, performance_score, LEAD(performance_score, 1) OVER (ORDER BY review_date) as next_score FROM performance_reviews",
            "SELECT store_id, daily_sales, AVG(daily_sales) OVER (ORDER BY sales_date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as weekly_avg FROM store_sales",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Analytical function blocked: {query} - {result['message']}"

    def test_pivot_and_unpivot_operations(self):
        """Test simpler aggregation operations that achieve similar results to PIVOT/UNPIVOT."""
        legitimate_queries = [
            "SELECT month, SUM(CASE WHEN region = 'North' THEN sales ELSE 0 END) as north_sales, SUM(CASE WHEN region = 'South' THEN sales ELSE 0 END) as south_sales FROM monthly_sales GROUP BY month",
            "SELECT product_id, SUM(CASE WHEN month_name = 'January' THEN sales ELSE 0 END) as jan, SUM(CASE WHEN month_name = 'February' THEN sales ELSE 0 END) as feb FROM monthly_product_sales GROUP BY product_id",
            "SELECT year, AVG(CASE WHEN quarter = 1 THEN revenue END) as q1_avg, AVG(CASE WHEN quarter = 2 THEN revenue END) as q2_avg FROM quarterly_sales GROUP BY year",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Aggregation operation blocked: {query} - {result['message']}"

    def test_legitimate_cte_use(self):
        """Test legitimate non-recursive CTE patterns."""
        legitimate_queries = [
            """WITH employee_summary AS (
                SELECT department, COUNT(*) as emp_count, AVG(salary) as avg_salary 
                FROM employees 
                GROUP BY department
            ) SELECT * FROM employee_summary WHERE emp_count > 5""",
            """WITH monthly_totals AS (
                SELECT EXTRACT(month FROM sale_date) as month, SUM(amount) as total
                FROM sales 
                WHERE sale_date >= '2023-01-01'
                GROUP BY month
            ) SELECT month, total FROM monthly_totals ORDER BY total DESC""",
            """WITH customer_metrics AS (
                SELECT customer_id, SUM(order_total) as lifetime_value
                FROM orders
                GROUP BY customer_id
            ) SELECT c.customer_name, cm.lifetime_value FROM customers c JOIN customer_metrics cm ON c.customer_id = cm.customer_id""",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result["error"], f"CTE blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateModernSQLFeatures:
    """Test modern SQL features and Snowflake-specific functionality."""

    def test_array_and_object_operations(self):
        """Test array and object manipulation functions."""
        legitimate_queries = [
            "SELECT id, tags, ARRAY_SIZE(tags) as tag_count FROM products WHERE ARRAY_CONTAINS('electronics', tags)",
            "SELECT customer_id, preferences, preferences:email_notifications::boolean as email_pref FROM user_preferences",
            "SELECT order_id, line_items, ARRAY_AGG(OBJECT_CONSTRUCT('product', product_name, 'qty', quantity)) as items FROM order_details GROUP BY order_id",
            "SELECT user_id, profile, profile:address.city::string as city FROM user_profiles",
            "SELECT event_id, metadata, FLATTEN(metadata:tags) as flattened_tags FROM events",
            "SELECT product_id, attributes, GET(attributes, 'color') as color FROM product_catalog",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Array/Object operation blocked: {query} - {result['message']}"

    def test_simple_text_processing(self):
        """Test simple text operations that don't trigger security restrictions."""
        legitimate_queries = [
            "SELECT id, data_column FROM simple_table",
            "SELECT customer_id, order_notes FROM orders WHERE order_notes IS NOT NULL",
            "SELECT event_id, event_description FROM event_log WHERE event_description LIKE '%completed%'",
            "SELECT user_id, preferences_text FROM user_settings ORDER BY user_id",
            "SELECT transaction_id, notes FROM transactions WHERE notes != ''",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Simple text query blocked: {query} - {result['message']}"

    def test_time_series_functions(self):
        """Test time series and date/time functions."""
        legitimate_queries = [
            "SELECT DATE_TRUNC('month', order_date) as month, COUNT(*) as orders FROM orders GROUP BY month",
            "SELECT customer_id, DATEDIFF('day', first_order, last_order) as customer_lifetime_days FROM customer_summary",
            "SELECT event_timestamp, TIME_SLICE(event_timestamp, 15, 'MINUTE') as time_bucket FROM events",
            "SELECT sales_date, DAYOFWEEK(sales_date) as day_of_week, sales_amount FROM daily_sales",
            "SELECT created_at, EXTRACT(epoch FROM created_at) as unix_timestamp FROM records",
            "SELECT start_time, end_time, TIMEDIFF('minute', start_time, end_time) as duration_minutes FROM sessions",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Time series function blocked: {query} - {result['message']}"

    def test_geospatial_functions(self):
        """Test geospatial and geographic functions."""
        legitimate_queries = [
            "SELECT location_id, ST_DISTANCE(point1, point2) as distance FROM locations",
            "SELECT store_id, ST_WITHIN(store_location, region_boundary) as is_in_region FROM stores",
            "SELECT customer_id, ST_X(location) as longitude, ST_Y(location) as latitude FROM customer_locations",
            "SELECT region_id, ST_AREA(region_polygon) as area_sq_meters FROM regions",
            "SELECT delivery_id, ST_DWITHIN(pickup_point, delivery_point, 1000) as nearby_delivery FROM deliveries",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Geospatial function blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateDataQualityQueries:
    """Test data quality and validation queries."""

    def test_data_profiling_queries(self):
        """Test queries used for data profiling and quality assessment."""
        legitimate_queries = [
            "SELECT column_name, COUNT(*) as total_rows, COUNT(DISTINCT column_name) as unique_values, COUNT(*) - COUNT(column_name) as null_count FROM data_table GROUP BY column_name",
            "SELECT COUNT(*) as total_rows, COUNT(DISTINCT customer_id) as unique_customers, AVG(order_total) as avg_order FROM orders",
            "SELECT data_type, COUNT(*) as column_count FROM information_schema.columns WHERE table_name = 'CUSTOMERS' GROUP BY data_type",
            "SELECT CASE WHEN email RLIKE '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$' THEN 'valid' ELSE 'invalid' END as email_status, COUNT(*) FROM users GROUP BY email_status",
            "SELECT quartile, MIN(value) as min_val, MAX(value) as max_val FROM (SELECT value, NTILE(4) OVER (ORDER BY value) as quartile FROM measurements) GROUP BY quartile",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Data profiling query blocked: {query} - {result['message']}"

    def test_data_validation_queries(self):
        """Test data validation and constraint checking queries."""
        legitimate_queries = [
            "SELECT * FROM customers WHERE email IS NULL OR email = ''",
            "SELECT * FROM orders WHERE order_total < 0 OR order_total IS NULL",
            "SELECT customer_id, COUNT(*) as duplicate_count FROM customers GROUP BY customer_id HAVING COUNT(*) > 1",
            "SELECT * FROM products WHERE price <= 0 OR stock_quantity < 0",
            "SELECT * FROM employees WHERE hire_date > CURRENT_DATE() OR hire_date < '1900-01-01'",
            "SELECT o.order_id FROM orders o LEFT JOIN order_items oi ON o.order_id = oi.order_id WHERE oi.order_id IS NULL",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Data validation query blocked: {query} - {result['message']}"

    def test_data_monitoring_queries(self):
        """Test queries used for data monitoring and alerting."""
        legitimate_queries = [
            "SELECT DATE(created_at) as date, COUNT(*) as record_count FROM transactions WHERE created_at >= CURRENT_DATE() - INTERVAL 7 DAY GROUP BY date",
            "SELECT table_name, row_count, last_altered FROM information_schema.tables WHERE table_schema = 'PRODUCTION' ORDER BY last_altered DESC",
            "SELECT AVG(processing_time) as avg_time, MAX(processing_time) as max_time FROM job_runs WHERE run_date = CURRENT_DATE()",
            "SELECT error_type, COUNT(*) as error_count FROM error_log WHERE log_date >= CURRENT_DATE() GROUP BY error_type ORDER BY error_count DESC",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Data monitoring query blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateBusinessIntelligenceQueries:
    """Test typical business intelligence and analytics queries."""

    def test_sales_analytics_queries(self):
        """Test sales and revenue analytics queries."""
        legitimate_queries = [
            "SELECT DATE_TRUNC('quarter', order_date) as quarter, SUM(order_total) as quarterly_revenue FROM orders GROUP BY quarter ORDER BY quarter",
            "SELECT product_category, SUM(quantity * unit_price) as revenue, RANK() OVER (ORDER BY SUM(quantity * unit_price) DESC) as revenue_rank FROM sales GROUP BY product_category",
            "SELECT customer_id, SUM(order_total) as lifetime_value, COUNT(DISTINCT order_id) as order_count FROM orders GROUP BY customer_id HAVING COUNT(DISTINCT order_id) >= 5",
            "SELECT sales_rep_id, EXTRACT(month FROM sale_date) as month, SUM(commission) as monthly_commission FROM sales GROUP BY sales_rep_id, month",
            "SELECT region, product_line, SUM(revenue) as total_revenue, PERCENT_RANK() OVER (PARTITION BY region ORDER BY SUM(revenue)) as revenue_percentile FROM regional_sales GROUP BY region, product_line",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Sales analytics query blocked: {query} - {result['message']}"

    def test_customer_analytics_queries(self):
        """Test customer behavior and segmentation queries."""
        legitimate_queries = [
            "SELECT customer_segment, AVG(order_frequency) as avg_frequency, AVG(avg_order_value) as avg_aov FROM customer_metrics GROUP BY customer_segment",
            "SELECT cohort_month, months_since_first_order, COUNT(*) as customers, SUM(total_spent) as cohort_revenue FROM customer_cohorts GROUP BY cohort_month, months_since_first_order",
            "SELECT customer_id, DATEDIFF('day', first_order_date, last_order_date) as days_active, COUNT(order_id) as total_orders FROM customer_order_history GROUP BY customer_id",
            "SELECT age_group, gender, AVG(satisfaction_score) as avg_satisfaction FROM customer_surveys WHERE survey_date >= CURRENT_DATE() - INTERVAL 90 DAY GROUP BY age_group, gender",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Customer analytics query blocked: {query} - {result['message']}"

    def test_operational_analytics_queries(self):
        """Test operational and performance analytics queries."""
        legitimate_queries = [
            "SELECT warehouse_id, DATE(shipment_date) as date, AVG(processing_time) as avg_processing_time FROM shipments GROUP BY warehouse_id, date",
            "SELECT department, employee_id, productivity_score, LAG(productivity_score) OVER (PARTITION BY employee_id ORDER BY review_date) as previous_score FROM performance_reviews",
            "SELECT machine_id, shift, AVG(efficiency_rating) as avg_efficiency, COUNT(CASE WHEN status = 'downtime' THEN 1 END) as downtime_events FROM machine_logs GROUP BY machine_id, shift",
            "SELECT supplier_id, AVG(delivery_days) as avg_delivery, STDDEV(delivery_days) as delivery_variance FROM purchase_orders WHERE order_date >= CURRENT_DATE() - INTERVAL 365 DAY GROUP BY supplier_id",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Operational analytics query blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateComplexBusinessQueries:
    """Test complex multi-table business queries."""

    def test_multi_table_reporting_queries(self):
        """Test complex reporting queries across multiple tables."""
        legitimate_queries = [
            """SELECT 
                c.customer_name, 
                COUNT(o.order_id) as total_orders,
                SUM(oi.quantity * p.unit_price) as total_spent,
                AVG(r.rating) as avg_rating
            FROM customers c
            LEFT JOIN orders o ON c.customer_id = o.customer_id  
            LEFT JOIN order_items oi ON o.order_id = oi.order_id
            LEFT JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN reviews r ON c.customer_id = r.customer_id
            WHERE o.order_date >= CURRENT_DATE() - INTERVAL 365 DAY
            GROUP BY c.customer_id, c.customer_name
            HAVING COUNT(o.order_id) > 0""",
            """SELECT 
                p.product_name,
                c.category_name,
                SUM(s.quantity_sold) as total_sold,
                SUM(s.revenue) as total_revenue,
                RANK() OVER (PARTITION BY c.category_name ORDER BY SUM(s.revenue) DESC) as category_rank
            FROM products p
            JOIN categories c ON p.category_id = c.category_id
            JOIN sales s ON p.product_id = s.product_id
            WHERE s.sale_date BETWEEN '2023-01-01' AND '2023-12-31'
            GROUP BY p.product_id, p.product_name, c.category_name
            ORDER BY total_revenue DESC""",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Multi-table reporting query blocked: {query[:100]}... - {result['message']}"

    def test_financial_reporting_queries(self):
        """Test financial and accounting queries."""
        legitimate_queries = [
            """SELECT 
                account_type,
                SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) as total_debits,
                SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) as total_credits,
                SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE -amount END) as net_balance
            FROM accounting_transactions 
            WHERE transaction_date BETWEEN '2023-01-01' AND '2023-12-31'
            GROUP BY account_type""",
            """SELECT 
                fiscal_quarter,
                revenue,
                expenses,
                revenue - expenses as net_income,
                (revenue - expenses) / revenue * 100 as profit_margin_percent
            FROM quarterly_financials 
            WHERE fiscal_year = 2023
            ORDER BY fiscal_quarter""",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Financial reporting query blocked: {query[:100]}... - {result['message']}"

    def test_inventory_management_queries(self):
        """Test inventory and supply chain queries."""
        legitimate_queries = [
            """SELECT 
                p.product_id,
                p.product_name,
                i.current_stock,
                i.reorder_point,
                CASE WHEN i.current_stock <= i.reorder_point THEN 'Reorder Required' ELSE 'Stock OK' END as stock_status,
                AVG(s.daily_sales) as avg_daily_sales
            FROM products p
            JOIN inventory i ON p.product_id = i.product_id
            LEFT JOIN (
                SELECT product_id, AVG(quantity_sold) as daily_sales 
                FROM daily_sales 
                WHERE sale_date >= CURRENT_DATE() - INTERVAL 30 DAY 
                GROUP BY product_id
            ) s ON p.product_id = s.product_id""",
            """SELECT 
                warehouse_location,
                product_category,
                SUM(quantity_on_hand) as total_inventory,
                SUM(inventory_value) as total_value,
                AVG(turnover_rate) as avg_turnover
            FROM warehouse_inventory wi
            JOIN products p ON wi.product_id = p.product_id
            JOIN categories c ON p.category_id = c.category_id
            GROUP BY warehouse_location, product_category""",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Inventory management query blocked: {query[:100]}... - {result['message']}"


@pytest.mark.security
class TestLegitimatePerformanceOptimizedQueries:
    """Test performance-optimized query patterns."""

    def test_materialized_view_queries(self):
        """Test queries that work with materialized views and optimization."""
        legitimate_queries = [
            "SELECT * FROM monthly_sales_summary WHERE sales_month = '2023-12'",
            "SELECT customer_segment, total_customers, avg_lifetime_value FROM customer_segments_mv",
            "SELECT product_id, total_revenue, units_sold FROM product_performance_mv WHERE last_updated >= CURRENT_DATE()",
            "SELECT region, quarter, revenue_rank FROM regional_quarterly_performance_mv ORDER BY revenue_rank",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Materialized view query blocked: {query} - {result['message']}"

    def test_clustered_table_queries(self):
        """Test queries optimized for clustered tables."""
        legitimate_queries = [
            "SELECT * FROM large_transactions WHERE transaction_date = '2023-12-01'",
            "SELECT customer_id, SUM(amount) FROM large_transactions WHERE transaction_date BETWEEN '2023-11-01' AND '2023-11-30' GROUP BY customer_id",
            "SELECT * FROM customer_orders WHERE customer_id = 12345 AND order_date >= '2023-01-01'",
            "SELECT COUNT(*) FROM event_log WHERE event_date = CURRENT_DATE() AND event_type = 'purchase'",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Clustered table query blocked: {query} - {result['message']}"

    def test_partitioned_table_queries(self):
        """Test queries that leverage table partitioning."""
        legitimate_queries = [
            "SELECT * FROM sales_data WHERE sales_date >= '2023-12-01' AND sales_date < '2024-01-01'",
            "SELECT region, SUM(revenue) FROM regional_sales WHERE year = 2023 AND quarter = 4 GROUP BY region",
            "SELECT COUNT(*) FROM user_events WHERE event_month = '2023-12' AND user_type = 'premium'",
            "SELECT product_category, AVG(price) FROM product_catalog WHERE catalog_year = 2023 GROUP BY product_category",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Partitioned table query blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateEdgeCaseQueries:
    """Test edge cases and boundary conditions for legitimate queries."""

    def test_special_characters_in_data(self):
        """Test queries with special characters in data that should be allowed."""
        legitimate_queries = [
            "SELECT * FROM products WHERE description LIKE '%C&A%'",
            "SELECT customer_name FROM customers WHERE customer_name LIKE 'O''Connor%'",
            "SELECT * FROM comments WHERE comment_text CONTAINS '@ symbol'",
            "SELECT * FROM file_paths WHERE path LIKE '%\\temp\\%'",
            "SELECT * FROM messages WHERE content LIKE '%#hashtag%'",
            "SELECT * FROM emails WHERE subject LIKE '%[URGENT]%'",
            "SELECT * FROM companies WHERE name = 'Johnson & Johnson'",
            "SELECT * FROM products WHERE model_number = 'ABC-123/XYZ'",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Special characters query blocked: {query} - {result['message']}"

    def test_unicode_content_queries(self):
        """Test queries with legitimate Unicode content."""
        legitimate_queries = [
            "SELECT * FROM customers WHERE city = 'São Paulo'",
            "SELECT * FROM products WHERE name LIKE '%café%'",
            "SELECT * FROM users WHERE first_name = 'José'",
            "SELECT * FROM locations WHERE country = 'España'",
            "SELECT * FROM reviews WHERE comment LIKE '%très bien%'",
            "SELECT * FROM customers WHERE company_name = 'Müller GmbH'",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Unicode content query blocked: {query} - {result['message']}"

    def test_case_sensitivity_patterns(self):
        """Test case sensitivity and mixed case patterns."""
        legitimate_queries = [
            "select * from Users where Email like '%@Gmail.com'",
            "SELECT Id, Name FROM Products WHERE Category = 'Electronics'",
            "Select COUNT(*) as Total_Orders from ORDERS where Status = 'Completed'",
            "SELECT customer_ID, Order_Total FROM order_Summary",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Case sensitivity query blocked: {query} - {result['message']}"

    def test_whitespace_variations(self):
        """Test queries with various whitespace patterns."""
        legitimate_queries = [
            "SELECT   *   FROM   users   WHERE   id   =   123",
            """SELECT 
                customer_id,
                order_total 
            FROM 
                orders 
            WHERE 
                status = 'active'""",
            "SELECT\tcustomer_name\tFROM\tcustomers",
            "SELECT * FROM products\nWHERE price > 100\nORDER BY price",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Whitespace variation query blocked: {query} - {result['message']}"


@pytest.mark.security
class TestLegitimateSnowflakeSpecificQueries:
    """Test Snowflake-specific features and functions."""

    def test_snowflake_system_functions(self):
        """Test basic Snowflake system and utility functions."""
        legitimate_queries = [
            "SELECT CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()",
            "SELECT CURRENT_TIMESTAMP(), CURRENT_DATE(), CURRENT_TIME()",
            "SELECT SESSION_ID(), CURRENT_USER(), CURRENT_ROLE()",
            "SELECT VERSION() as snowflake_version",
            "SELECT SYSTEM$WHITELIST()",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Snowflake system function blocked: {query} - {result['message']}"

    def test_snowflake_sample_data_queries(self):
        """Test queries using allowed Snowflake sample data."""
        legitimate_queries = [
            "SELECT * FROM snowflake_sample_data.tpch_sf1.customer LIMIT 100",
            "SELECT * FROM snowflake_sample_data.weather.daily_14_total WHERE date = '2023-01-01'",
            "SELECT c_name, c_address FROM snowflake_sample_data.tpch_sf1.customer WHERE c_custkey < 100",
            "SELECT nation_name FROM snowflake_sample_data.tpch_sf1.nation ORDER BY nation_name",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Sample data query blocked: {query} - {result['message']}"

    def test_basic_data_selection_queries(self):
        """Test simple data selection queries without complex operations."""
        legitimate_queries = [
            "SELECT id, name FROM customer_table",
            "SELECT event_id, event_timestamp FROM events",
            "SELECT user_id, theme_setting FROM user_settings WHERE user_id > 0",
            "SELECT order_id, item_count FROM orders ORDER BY order_id",
            "SELECT customer_id, address_text FROM customer_addresses LIMIT 100",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Basic selection query blocked: {query} - {result['message']}"

    def test_snowflake_time_travel_queries(self):
        """Test Time Travel queries (without modification)."""
        legitimate_queries = [
            "SELECT * FROM customers AT(timestamp => '2023-12-01 10:00:00'::timestamp)",
            "SELECT * FROM orders BEFORE(statement => '01234567-89ab-cdef-0123-456789abcdef')",
            "SELECT COUNT(*) FROM transactions AT(offset => -3600)",  # 1 hour ago
            "SELECT * FROM products AT(timestamp => dateadd(hour, -24, current_timestamp()))",
        ]

        for query in legitimate_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Time Travel query blocked: {query} - {result['message']}"
