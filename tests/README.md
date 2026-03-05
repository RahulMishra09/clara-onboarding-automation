# Clara AI Automation - Test Suite

## Overview

This directory contains automated tests for the Clara AI Automation Pipeline.

## Test Files

### `test_schemas.py`
Tests for Pydantic data models and schema validation.

**Coverage:**
- AccountMemo creation and validation
- RetellAgentSpec creation and validation
- Changelog creation and validation
- BusinessHours nested schema
- EmergencyRoutingRules nested schema
- ProcessingMetadata schema
- Version enums

### `test_validators.py`
Tests for validation utilities and quality checks.

**Coverage:**
- Data quality validation
- Agent spec safety checks
- Hallucination detection
- Protocol completeness validation
- Forbidden term detection

### `test_storage.py`
Tests for the storage layer.

**Coverage:**
- Saving and loading v1/v2 memos
- Saving and loading agent specs
- Changelog storage
- Metadata tracking
- Account discovery
- Status queries
- Storage summaries

## Running Tests

### Run All Tests

```bash
cd /Users/rahulmishra/Desktop/clara-onboarding-automation
source venv/bin/activate
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_schemas.py -v
pytest tests/test_validators.py -v
pytest tests/test_storage.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_schemas.py::TestAccountMemo -v
```

### Run Specific Test Function

```bash
pytest tests/test_schemas.py::TestAccountMemo::test_valid_v1_memo -v
```

### Run with Coverage

```bash
pytest tests/ --cov=scripts --cov-report=html
open htmlcov/index.html
```

## Test Output

### Successful Run Example

```
================================ test session starts =================================
platform darwin -- Python 3.11.5, pytest-9.0.2, pluggy-1.6.0
collected 35 items

tests/test_schemas.py::TestAccountMemo::test_valid_v1_memo PASSED           [  2%]
tests/test_schemas.py::TestAccountMemo::test_valid_v2_memo_with_business_hours PASSED [  5%]
tests/test_schemas.py::TestAccountMemo::test_memo_with_integration_constraints PASSED [  8%]
tests/test_schemas.py::TestAccountMemo::test_memo_validation PASSED         [ 11%]
...

============================== 35 passed in 1.23s ================================
```

### Failed Test Example

```
================================= FAILURES =======================================
________________________ TestAccountMemo.test_valid_v1_memo _______________________

    def test_valid_v1_memo(self):
        memo = AccountMemo(
            account_id="test-account",
            company_name="Test Company",
            version=Version.V1,
            questions_or_unknowns=["missing: business hours"]
        )
>       assert memo.account_id == "wrong-id"
E       AssertionError: assert 'test-account' == 'wrong-id'

tests/test_schemas.py:42: AssertionError
============================== 1 failed, 34 passed in 1.23s =======================
```

## Writing New Tests

### Test Structure

```python
import pytest
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from your_module import YourClass

class TestYourClass:
    """Test YourClass functionality."""

    def test_something(self):
        """Test that something works."""
        obj = YourClass()
        assert obj.method() == expected_value
```

### Using Fixtures

```python
@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """Test using the fixture."""
    assert sample_data["key"] == "value"
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test1", "result1"),
    ("test2", "result2"),
    ("test3", "result3"),
])
def test_multiple_inputs(input, expected):
    """Test with multiple input/output pairs."""
    assert process(input) == expected
```

## Test Categories

### Unit Tests
Test individual functions and classes in isolation.
- All current tests are unit tests
- Fast execution
- No external dependencies

### Integration Tests (Future)
Test multiple components working together.
- Pipeline end-to-end tests
- LLM integration tests (with mocking)
- Storage + pipeline integration

### End-to-End Tests (Future)
Test complete workflows.
- Full demo → v1 processing
- Full onboarding → v2 processing
- Batch processing tests

## Mocking External Services

For tests that would normally call external APIs (LLM providers):

```python
from unittest.mock import Mock, patch

def test_llm_extraction():
    """Test extraction with mocked LLM."""
    with patch('llm_client.LLMClient') as mock_llm:
        mock_llm.return_value.complete.return_value = '{"account_id": "test"}'

        result = extract_memo(transcript)
        assert result["account_id"] == "test"
```

## Continuous Integration

### GitHub Actions (Example)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

## Test Coverage Goals

- **Schemas:** 100% coverage ✅
- **Validators:** 90%+ coverage ✅
- **Storage:** 95%+ coverage ✅
- **Pipelines:** 80%+ coverage (future)
- **LLM Integration:** 70%+ coverage (future, with mocking)

## Current Coverage

Run to see current coverage:

```bash
pytest tests/ --cov=scripts --cov-report=term-missing
```

Example output:
```
Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
scripts/config.py              50      5    90%   45-50
scripts/schemas.py            150      0   100%
scripts/validators.py         100      5    95%   85, 92
scripts/storage.py            200     10    95%   150-160
---------------------------------------------------------
TOTAL                         500     20    96%
```

## Common Issues

### Issue: "ModuleNotFoundError"

**Solution:** Make sure you're in the project root and venv is activated:
```bash
cd /Users/rahulmishra/Desktop/clara-onboarding-automation
source venv/bin/activate
pytest tests/
```

### Issue: "No tests collected"

**Solution:** Check that test files start with `test_` and functions start with `test_`:
```python
# ✅ Good
def test_something():
    pass

# ❌ Bad
def check_something():
    pass
```

### Issue: Import errors in tests

**Solution:** The test files add scripts/ to sys.path. If this doesn't work, you can also run:
```bash
PYTHONPATH=scripts pytest tests/
```

## Best Practices

1. **One assertion per test** (when possible)
2. **Clear test names** that describe what's being tested
3. **Use fixtures** for reusable test data
4. **Mock external dependencies** (APIs, databases, etc.)
5. **Test both success and failure cases**
6. **Keep tests fast** (unit tests should run in milliseconds)
7. **Test edge cases** (empty inputs, None values, etc.)

## Adding Tests for New Features

When adding new functionality:

1. Write tests first (TDD approach) or alongside code
2. Test happy path (normal usage)
3. Test error cases
4. Test edge cases
5. Run tests before committing
6. Aim for >90% coverage

## Future Test Additions

### Planned Tests

1. **test_pipelines.py** - Pipeline A & B tests
2. **test_extract_memo.py** - Extraction logic tests (with mocked LLM)
3. **test_generate_prompt.py** - Prompt generation tests
4. **test_apply_updates.py** - Merge logic tests
5. **test_batch_process.py** - Batch processing tests
6. **test_integration.py** - End-to-end integration tests

### Test Data

Create a `test_data/` directory with sample transcripts:
- `test_data/demo_sample.txt`
- `test_data/onboarding_sample.txt`
- `test_data/expected_v1_memo.json`
- `test_data/expected_v2_memo.json`

## Resources

- **pytest documentation:** https://docs.pytest.org
- **pytest fixtures:** https://docs.pytest.org/en/stable/fixture.html
- **pytest parametrize:** https://docs.pytest.org/en/stable/parametrize.html
- **Coverage.py:** https://coverage.readthedocs.io

---

**Run tests regularly to ensure code quality!** ✅
