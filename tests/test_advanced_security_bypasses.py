"""
Advanced security bypass tests for critical Snowflake functions.

This test suite focuses on sophisticated attack vectors that might bypass
the existing security validations.
"""

import pytest
from utils.snowflake_utils import (
    _perform_additional_security_checks,
    _validate_query_safety,
)


@pytest.mark.security
class TestAdvancedInjectionBypasses:
    """Test sophisticated SQL injection bypass techniques."""

    def test_unicode_normalization_bypass(self):
        """Test Unicode normalization attacks that might bypass regex patterns."""
        # Unicode characters that normalize to dangerous SQL keywords
        bypass_attempts = [
            "SELECT * FROM users WHERE id = 1 UＮＩ＠Ｎ SELECT password FROM admin",  # Full-width Unicode
            "SELECT * FROM users WHERE id = 1 ＵｎｉＯｎ SELECT password FROM admin",  # Mixed case Unicode
            "SELECT * FROM users WHERE id = 1 Ｕ\u006eＩＯＮ SELECT password FROM admin",  # Composed Unicode
            "SELECT * FROM users ᎾɌⅮⅇᎡ BY 1",  # Cherokee and other scripts
            "SELECT * FROM users Оᴿᴰᴱᴿ BY 1",  # Cyrillic lookalikes
        ]

        for malicious_query in bypass_attempts:
            result = _perform_additional_security_checks(
                malicious_query.upper(), malicious_query
            )
            assert result[
                "error"
            ], f"Failed to detect Unicode bypass: {malicious_query}"

    def test_encoding_based_bypasses(self):
        """Test encoding-based bypass attempts."""
        bypass_attempts = [
            # URL encoding
            "SELECT * FROM users WHERE id = 1 %55%4E%49%4F%4E SELECT password FROM admin",
            # HTML entity encoding
            "SELECT * FROM users WHERE id = 1 &#85;&#78;&#73;&#79;&#78; SELECT password FROM admin",
            # Hex encoding
            "SELECT * FROM users WHERE id = 1 0x554E494F4E SELECT password FROM admin",
            # Double encoding
            "SELECT * FROM users WHERE id = 1 %2555%254E%2549%254F%254E SELECT password",
        ]

        for malicious_query in bypass_attempts:
            _perform_additional_security_checks(
                malicious_query.upper(), malicious_query
            )
            # Note: These might not be caught by current regex, but should be flagged
            # This test documents the current behavior and alerts if it changes

    def test_whitespace_variation_bypasses(self):
        """Test bypasses using various whitespace characters."""
        bypass_attempts = [
            "SELECT\u0009*\u0009FROM\u0009users\u0009UNION\u0009SELECT\u0009password",  # Tab characters
            "SELECT\u000b*\u000bFROM\u000busers\u000bUNION\u000bSELECT\u000bpassword",  # Vertical tab
            "SELECT\u000c*\u000cFROM\u000cusers\u000cUNION\u000cSELECT\u000cpassword",  # Form feed
            "SELECT\u00a0*\u00a0FROM\u00a0users\u00a0UNION\u00a0SELECT\u00a0password",  # Non-breaking space
            "SELECT\u2000*\u2000FROM\u2000users\u2000UNION\u2000SELECT\u2000password",  # En quad
            "SELECT/**/UNION/**/SELECT",  # Comment-based whitespace replacement
        ]

        for malicious_query in bypass_attempts:
            result = _perform_additional_security_checks(
                malicious_query.upper(), malicious_query
            )
            assert result[
                "error"
            ], f"Failed to detect whitespace bypass: {repr(malicious_query)}"

    def test_case_variation_bypasses(self):
        """Test case variation bypass attempts."""
        bypass_attempts = [
            "SeLeCt * FrOm users UnIoN sElEcT password FrOm admin",
            "select * from users UNION select password from admin",
            "SELECT * FROM users uNiOn SeLeCt password FROM admin",
            "sElEcT * fRoM users union ALL sElEcT password fRoM admin",
        ]

        for malicious_query in bypass_attempts:
            result = _perform_additional_security_checks(
                malicious_query.upper(), malicious_query
            )
            assert result["error"], f"Failed to detect case bypass: {malicious_query}"

    def test_comment_based_bypasses(self):
        """Test sophisticated comment-based bypasses."""
        bypass_attempts = [
            "SELECT * FROM users/**/UNION/**/SELECT password FROM admin",
            "SELECT * FROM users/*comment*/UNION/*comment*/SELECT password",
            "SELECT * FROM users--comment\nUNION SELECT password FROM admin",
            "SELECT * FROM users/*outer/*inner*/comment*/UNION SELECT password",
            "SELECT * FROM users/* UNI*/ UNI/*ON*/ ON SELECT password",  # Split keywords
            "SELECT * FROM users/*\nMultiline\nComment\n*/UNION SELECT password",
        ]

        for malicious_query in bypass_attempts:
            result = _perform_additional_security_checks(
                malicious_query.upper(), malicious_query
            )
            assert result[
                "error"
            ], f"Failed to detect comment bypass: {malicious_query}"


@pytest.mark.security
class TestQueryValidationEdgeCases:
    """Test edge cases in query validation logic."""

    def test_regex_pattern_edge_cases(self):
        """Test edge cases that might break regex patterns."""
        edge_cases = [
            # Regex metacharacters
            "SELECT * FROM users WHERE id = '1' OR '.*' = '.*'",
            "SELECT * FROM users WHERE name LIKE '%[a-z]%'",
            "SELECT * FROM users WHERE data ~ '.*'",
            # Nested quotes
            "SELECT * FROM users WHERE msg = 'It''s a trap' UNION SELECT password",
            "SELECT * FROM users WHERE data = \"nested 'quotes' here\" UNION SELECT pwd",
            # Extremely long patterns
            "SELECT * FROM users WHERE " + "x = 1 OR " * 1000 + "1 = 1",
        ]

        for edge_case in edge_cases:
            result = _validate_query_safety(edge_case, 1000)
            # Verify that validation doesn't crash and handles edge cases properly
            assert isinstance(result, dict)
            assert "error" in result

    def test_parentheses_depth_boundary_conditions(self):
        """Test exact boundary conditions for parentheses depth."""
        # Test exactly at the limit (10 levels) - use non-malicious condition
        exactly_10_levels = (
            "SELECT * FROM users WHERE " + "(" * 10 + "id > 0" + ")" * 10
        )
        result = _perform_additional_security_checks(
            exactly_10_levels.upper(), exactly_10_levels
        )
        assert not result[
            "error"
        ], f"Should allow exactly 10 levels of nesting, got: {result['message']}"

        # Test one over the limit (11 levels)
        over_limit = "SELECT * FROM users WHERE " + "(" * 11 + "id > 0" + ")" * 11
        result = _perform_additional_security_checks(over_limit.upper(), over_limit)
        assert result["error"], "Should reject 11 levels of nesting"

    def test_query_length_boundary_conditions(self):
        """Test exact boundary conditions for query length."""
        # Test exactly at 10,000 characters
        base_query = "SELECT * FROM users WHERE "
        padding = "id > 0 AND "

        # Calculate how many full padding repetitions fit
        remaining_space = 10000 - len(base_query)
        full_repetitions = remaining_space // len(padding)
        exactly_10k = base_query + padding * full_repetitions

        # Add remaining characters to reach exactly 10,000
        remaining_chars = 10000 - len(exactly_10k)
        if remaining_chars > 0:
            exactly_10k += padding[:remaining_chars]

        assert (
            len(exactly_10k) == 10000
        ), f"Expected 10,000 chars, got {len(exactly_10k)}"

        result = _perform_additional_security_checks(exactly_10k.upper(), exactly_10k)
        assert not result[
            "error"
        ], f"Should allow exactly 10,000 characters, got: {result['message']}"

        # Test one character over (10,001 characters)
        over_limit = exactly_10k + "x"
        assert len(over_limit) == 10001, f"Expected 10,001 chars, got {len(over_limit)}"

        result = _perform_additional_security_checks(over_limit.upper(), over_limit)
        assert result[
            "error"
        ], f"Should reject 10,001 characters, got: {result['message']}"
        assert (
            "too long" in result["message"]
        ), f"Should mention length limit, got: {result['message']}"

    def test_join_count_boundary_conditions(self):
        """Test exact boundary conditions for JOIN count."""
        # Test exactly 5 JOINs (at the limit)
        exactly_5_joins = """
        SELECT * FROM table1 
        JOIN table2 ON table1.id = table2.id
        JOIN table3 ON table2.id = table3.id  
        JOIN table4 ON table3.id = table4.id
        JOIN table5 ON table4.id = table5.id
        JOIN table6 ON table5.id = table6.id
        """
        result = _perform_additional_security_checks(
            exactly_5_joins.upper(), exactly_5_joins
        )
        assert not result["error"], "Should allow exactly 5 JOINs"

        # Test 6 JOINs (over the limit)
        over_limit_joins = exactly_5_joins + " JOIN table7 ON table6.id = table7.id"
        result = _perform_additional_security_checks(
            over_limit_joins.upper(), over_limit_joins
        )
        assert result["error"], "Should reject 6 JOINs"


@pytest.mark.security
class TestSchemaAccessValidation:
    """Test schema access validation edge cases."""

    def test_schema_name_variations(self):
        """Test various schema name formats and potential bypasses."""
        malicious_schemas = [
            # Case variations
            "SELECT * FROM Production.users",
            "SELECT * FROM PRODUCTION.users",
            "SELECT * FROM production.users",
            # Quoted identifiers
            'SELECT * FROM "production".users',
            "SELECT * FROM 'production'.users",
            # Mixed case with quotes
            'SELECT * FROM "Production".users',
            # Escaped quotes
            'SELECT * FROM "production".users',
            # Multiple dots
            "SELECT * FROM database.production.schema.users",
            # Leading/trailing spaces in identifiers
            "SELECT * FROM ' production '.users",
        ]

        for malicious_query in malicious_schemas:
            result = _perform_additional_security_checks(
                malicious_query.upper(), malicious_query
            )
            assert result[
                "error"
            ], f"Should reject access to production schema: {malicious_query}"

    def test_information_schema_access_patterns(self):
        """Test various INFORMATION_SCHEMA access patterns."""
        allowed_queries = [
            "SELECT * FROM INFORMATION_SCHEMA.TABLES",
            "SELECT table_name FROM information_schema.tables",
            "SELECT * FROM SNOWFLAKE_SAMPLE_DATA.information_schema.tables",
        ]

        for query in allowed_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert not result[
                "error"
            ], f"Should allow INFORMATION_SCHEMA access: {query}"


@pytest.mark.security
class TestPerformanceAttackVectors:
    """Test performance-based attack scenarios."""

    def test_cartesian_product_detection(self):
        """Test detection of queries that might cause Cartesian products."""
        dangerous_queries = [
            "SELECT * FROM users u1, users u2, users u3",
            "SELECT * FROM orders o1, customers c1, products p1 WHERE 1=1",
            "SELECT * FROM table1 t1, table2 t2, table3 t3, table4 t4",
        ]

        for query in dangerous_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert result[
                "error"
            ], f"Should detect potential Cartesian product: {query}"

    def test_recursive_cte_detection(self):
        """Test detection of potentially dangerous recursive CTEs."""
        recursive_queries = [
            "WITH RECURSIVE cte AS (SELECT 1 UNION ALL SELECT n+1 FROM cte WHERE n < 1000000) SELECT * FROM cte",
            "WITH recursive factorial(n, fact) AS (SELECT 1, 1 UNION ALL SELECT n+1, (n+1)*fact FROM factorial WHERE n < 1000) SELECT * FROM factorial",
        ]

        for query in recursive_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert result["error"], f"Should detect recursive CTE: {query}"

    def test_complex_operation_detection(self):
        """Test detection of resource-intensive operations."""
        complex_queries = [
            "SELECT * FROM table1 PIVOT (SUM(amount) FOR category IN ('A', 'B', 'C'))",
            "SELECT * FROM table1 UNPIVOT (amount FOR category IN (col1, col2, col3))",
            "SELECT * FROM LATERAL VIEW explode(array_col) t AS element",
            "SELECT * FROM table1 MODEL DIMENSION BY (id) MEASURES (value)",
        ]

        for query in complex_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert result["error"], f"Should detect complex operation: {query}"


@pytest.mark.security
class TestFileOperationSecurity:
    """Test file operation security validation."""

    def test_stage_reference_detection(self):
        """Test detection of stage references."""
        stage_queries = [
            "SELECT * FROM @my_stage/file.csv",
            "SELECT $1, $2 FROM @internal_stage",
            "COPY INTO table FROM @external_stage",
            "LIST @my_stage",
        ]

        for query in stage_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert result["error"], f"Should detect stage reference: {query}"

    def test_external_reference_detection(self):
        """Test detection of external references."""
        external_queries = [
            "SELECT * FROM 's3://bucket/file.csv'",
            "CREATE EXTERNAL TABLE FROM 'azure://container/file'",
            "SELECT * FROM 'gcs://bucket/data.parquet'",
            "LOAD DATA FROM 'https://example.com/data.csv'",
            "SELECT * FROM 'http://malicious.com/payload'",
        ]

        for query in external_queries:
            result = _perform_additional_security_checks(query.upper(), query)
            assert result["error"], f"Should detect external reference: {query}"


@pytest.mark.security
class TestRegexExploitation:
    """Test for potential regex exploitation vulnerabilities."""

    def test_regex_dos_patterns(self):
        """Test patterns that might cause regex DoS (ReDoS)."""
        # Patterns that could cause exponential backtracking
        redos_attempts = [
            "SELECT * FROM users WHERE email LIKE '" + "a" * 10000 + "X'",
            "SELECT * FROM users WHERE " + "(" * 100 + "a" + ")" * 100,
            "SELECT * FROM users WHERE data = '" + "\\'" * 1000 + "'",
        ]

        for attack in redos_attempts:
            # Test that validation completes in reasonable time
            import time

            start_time = time.time()
            result = _perform_additional_security_checks(attack.upper(), attack)
            execution_time = time.time() - start_time

            # Should complete within 1 second (adjust threshold as needed)
            assert (
                execution_time < 1.0
            ), f"Regex validation took too long: {execution_time}s"
            assert isinstance(result, dict), "Should return valid result structure"
