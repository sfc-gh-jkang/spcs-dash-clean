# Test Suite for Snowflake Dash Analytics App

This directory contains comprehensive tests for the Snowflake Dash Analytics application, with a focus on the `snowflake_utils` module.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest fixtures and configuration
├── test_snowflake_utils.py     # Main unit tests for snowflake_utils
├── test_security.py            # Comprehensive security validation tests
├── test_security_stress.py     # Security stress tests and edge cases
├── test_integration.py         # Integration tests
└── README.md                   # This file
```

## Test Categories

### Unit Tests (`test_snowflake_utils.py`)
- **Environment Detection**: Tests for SPCS vs local environment detection
- **Snowflake Session Management**: Connection handling and session creation
- **Data Retrieval**: Schema objects, table lists, and table data fetching
- **Security Validation**: SQL injection prevention, keyword filtering
- **Rate Limiting**: Query frequency control
- **Query Execution**: Safe query execution with validation
- **Result Formatting**: AG Grid formatting and theming

### Security Tests (`test_security.py`)
- **SQL Injection Prevention**: Classic injection patterns, comment-based, UNION-based
- **Advanced SQL Injection**: Polyglot injection, blind injection, second-order injection
- **Access Control**: Schema restrictions, file operation prevention
- **Privilege Escalation Prevention**: Role manipulation, user manipulation, warehouse control
- **Data Exfiltration Prevention**: External stage access, information schema enumeration
- **Timing Attack Prevention**: Time delay injection, resource exhaustion
- **Bypass Techniques**: Comment evasion, encoding evasion, whitespace manipulation
- **Real-World Attack Scenarios**: Multi-stage attacks, data breach scenarios, insider threats
- **Edge Case Validation**: Unicode attacks, boundary values, deeply nested queries
- **Compliance Validation**: PII access patterns, audit trails, data residency

### Security Stress Tests (`test_security_stress.py`)
- **Concurrent Attack Load**: Multi-threaded malicious query execution
- **Large-Scale Validation**: Performance under massive attack datasets
- **Extreme Edge Cases**: Extremely long queries, deep nesting, Unicode normalization
- **Sophisticated Bypass Attempts**: Multi-vector attacks, timing-based bypasses
- **Security Audit**: Coverage completeness, false positive rates, consistency
- **Performance Under Load**: Scalability testing, concurrent validation performance

### Integration Tests (`test_integration.py`)
- **End-to-End Flows**: Complete query execution workflows
- **Error Handling**: Error propagation across components
- **Rate Limiting Integration**: Real-world rate limiting scenarios
- **Theme Integration**: Multi-theme result formatting
- **Large Dataset Handling**: Performance with large data
- **Environment Integration**: SPCS vs local environment workflows

## Running Tests

### All Tests
```bash
make test
# or
uv run pytest
```

### By Category
```bash
# Unit tests only
uv run pytest -m unit

# Security tests only
uv run pytest -m security

# Integration tests only
uv run pytest -m integration
```

### With Coverage
```bash
make test-coverage
# or
uv run pytest --cov=utils --cov-report=html
```

### Specific Test Files
```bash
# Run specific test file
uv run pytest tests/test_security.py

# Run specific test class
uv run pytest tests/test_snowflake_utils.py::TestSecurityValidation

# Run specific test
uv run pytest tests/test_snowflake_utils.py::TestEnvironmentDetection::test_is_running_in_spcs_true
```

### Fast Testing Options
```bash
# Stop on first failure
uv run pytest -x

# Run failed tests first
uv run pytest --ff

# Verbose output
uv run pytest -v -s
```

## Test Fixtures

The `conftest.py` file provides reusable fixtures:

- `sample_dataframe`: Standard test DataFrame
- `empty_dataframe`: Empty DataFrame for edge cases
- `error_dataframe`: DataFrame with error conditions
- `mock_snowflake_session`: Mock Snowflake session
- `safe_sql_queries`: Collection of safe SQL queries
- `dangerous_sql_queries`: Collection of malicious SQL queries
- `sql_injection_patterns`: Common injection patterns
- `large_datasets`: Factory for large test datasets

## Test Markers

Tests are marked with categories for selective execution:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.security`: Security-focused tests
- `@pytest.mark.slow`: Long-running tests

## Coverage Goals

Our test suite aims for:
- **90%+ code coverage** for all utility functions
- **100% coverage** for security validation functions
- **Complete edge case coverage** for input validation
- **Full error path testing** for all failure scenarios

## Mock Strategy

We use comprehensive mocking to:
- **Isolate units under test** from external dependencies
- **Simulate various Snowflake responses** (success, error, timeout)
- **Test edge cases** that are difficult to reproduce naturally
- **Ensure consistent test execution** across environments

## Security Test Philosophy

Security tests are designed to:
- **Verify all attack vectors are blocked**
- **Test for bypass attempts** using various techniques
- **Ensure defense in depth** across multiple validation layers
- **Validate error handling** doesn't leak sensitive information

## Running Tests in CI/CD

For continuous integration:

```bash
# Install dependencies
uv sync --group test

# Run all tests with coverage
uv run pytest --cov=utils --cov-report=xml --cov-fail-under=85

# Run security tests (critical for deployment)
uv run pytest -m security --tb=short
```

## Adding New Tests

When adding new functionality:

1. **Add unit tests** in `test_snowflake_utils.py`
2. **Add security tests** if the function handles user input
3. **Add integration tests** if the function interacts with external systems
4. **Update fixtures** in `conftest.py` if needed
5. **Use appropriate markers** for test categorization

## Debugging Failed Tests

For debugging:

```bash
# Run with verbose output and stop on first failure
uv run pytest -v -s -x

# Run specific failing test with full traceback
uv run pytest tests/test_file.py::test_function --tb=long

# Use pytest debugger
uv run pytest --pdb
```

## Performance Testing

For performance-sensitive functions:

```bash
# Run slow tests (includes performance tests)
uv run pytest -m slow

# Run with timing information
uv run pytest --durations=10
```
