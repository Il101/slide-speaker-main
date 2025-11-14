# Testing Guide for Slide Speaker

Comprehensive guide for testing Slide Speaker application.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [CI/CD Integration](#cicd-integration)
6. [Coverage Requirements](#coverage-requirements)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Backend Setup

```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### Frontend Setup

```bash
# Install dependencies
npm install

# Run tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

---

## 📁 Test Structure

```
backend/
├── pytest.ini              # Pytest configuration
├── conftest.py             # Shared fixtures
└── tests/
    ├── unit/               # Fast, isolated tests
    │   ├── test_provider_factory.py
    │   ├── test_pipeline_base.py
    │   ├── test_auth.py
    │   └── test_services.py
    ├── integration/        # Tests with DB/Redis
    │   ├── test_api_auth.py
    │   ├── test_api_lessons.py
    │   └── test_celery_tasks.py
    └── e2e/                # End-to-end tests
        └── test_full_flow.py

frontend/
└── src/
    └── test/
        ├── api.test.ts
        ├── components.test.tsx
        └── hooks.test.ts
```

---

## 🧪 Running Tests

### Backend Tests

#### Run All Tests
```bash
cd backend
pytest
```

#### Run Specific Test Suites
```bash
# Unit tests only (fast)
pytest tests/unit -v

# Integration tests only
pytest tests/integration -v

# E2E tests only
pytest tests/e2e -v
```

#### Run by Markers
```bash
# Run tests marked as @pytest.mark.unit
pytest -m unit

# Run tests marked as @pytest.mark.slow
pytest -m slow

# Run tests that require Google Cloud
pytest -m google_cloud
```

#### Run Specific Tests
```bash
# Run single test file
pytest tests/unit/test_provider_factory.py

# Run single test class
pytest tests/unit/test_provider_factory.py::TestProviderFactory

# Run single test function
pytest tests/unit/test_provider_factory.py::TestProviderFactory::test_get_ocr_provider_google
```

#### Run with Coverage
```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term-missing

# Check coverage threshold
pytest --cov=app --cov-fail-under=70

# Generate XML report (for CI/CD)
pytest --cov=app --cov-report=xml
```

#### Run in Parallel
```bash
# Use all CPU cores
pytest -n auto

# Use specific number of workers
pytest -n 4
```

#### Debug Tests
```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Stop at first failure
pytest -x

# Show slowest 10 tests
pytest --durations=10
```

### Frontend Tests

#### Run All Tests
```bash
npm test
```

#### Run with Coverage
```bash
npm run test:coverage
```

#### Run in Watch Mode
```bash
npm run test:watch
```

#### Run Specific Tests
```bash
# Run specific test file
npm test -- api.test.ts

# Run tests matching pattern
npm test -- --grep "Player"
```

---

## ✍️ Writing Tests

### Backend Test Example

#### Unit Test
```python
# tests/unit/test_my_service.py
import pytest
from unittest.mock import Mock

class TestMyService:
    """Test MyService class"""
    
    def test_basic_functionality(self):
        """Test basic service functionality"""
        from app.services.my_service import MyService
        
        service = MyService()
        result = service.process("input")
        
        assert result == "expected_output"
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async service functionality"""
        from app.services.my_service import MyService
        
        service = MyService()
        result = await service.async_process("input")
        
        assert result == "expected_output"
    
    def test_with_mock(self, mock_ocr_provider):
        """Test with mocked dependencies"""
        from app.services.my_service import MyService
        
        service = MyService(ocr_provider=mock_ocr_provider)
        result = service.process_with_ocr("image.png")
        
        mock_ocr_provider.extract.assert_called_once()
        assert result is not None
```

#### Integration Test
```python
# tests/integration/test_api_lessons.py
import pytest
from httpx import AsyncClient

@pytest.mark.integration
class TestLessonsAPI:
    """Test Lessons API endpoints"""
    
    async def test_create_lesson(self, test_client, test_user):
        """Test creating a new lesson"""
        response = await test_client.post(
            "/api/lessons",
            json={"title": "Test Lesson"},
            headers={"Authorization": f"Bearer {test_user['token']}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Lesson"
```

### Frontend Test Example

```typescript
// src/test/api.test.ts
import { describe, it, expect, vi } from 'vitest';
import { apiClient } from '@/lib/api';

describe('API Client', () => {
  it('should handle login successfully', async () => {
    const mockResponse = {
      message: 'Login successful',
      user: { email: 'test@example.com' }
    };
    
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse
    });
    
    const result = await apiClient.login({
      email: 'test@example.com',
      password: 'password'
    });
    
    expect(result).toEqual(mockResponse);
  });
});
```

---

## 🔄 CI/CD Integration

### GitHub Actions

Tests run automatically on:
- **Push** to `main`, `production-deploy`, `development`
- **Pull Requests** to `main`, `production-deploy`

### Pipeline Stages

1. **Backend Tests** - Unit + Integration + Coverage
2. **Frontend Tests** - Unit + Build + Bundle Size
3. **Security Scanning** - Bandit + npm audit + Secret detection
4. **Docker Build** - Build images + Test compose
5. **Smoke Tests** - Start services + Test health endpoints
6. **Code Quality** - SonarCloud analysis

### View Results

- **GitHub**: Check "Actions" tab in repository
- **Coverage**: View Codecov report in PR comments
- **Quality**: View SonarCloud report

---

## 📊 Coverage Requirements

### Minimum Coverage
- **Overall**: 70%
- **New Code**: 80%
- **Critical Modules**: 90%

### Critical Modules
- `app/core/auth.py`
- `app/core/database.py`
- `app/services/provider_factory.py`
- `app/pipeline/base.py`

### Check Coverage
```bash
# Backend
cd backend
pytest --cov=app --cov-report=term-missing

# View detailed report
open htmlcov/index.html

# Check if meets threshold
pytest --cov=app --cov-fail-under=70
```

---

## 🔧 Pre-commit Hooks

### Install Hooks
```bash
# Install pre-commit tool
pip install pre-commit

# Install hooks
pre-commit install

# Install commit message hook
pre-commit install --hook-type commit-msg
```

### Run Hooks Manually
```bash
# Run on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files

# Skip hooks (emergency only!)
git commit --no-verify
```

### Hooks Included
- **Formatting**: Black, isort, Prettier
- **Linting**: Flake8, Pylint, ESLint
- **Type Checking**: MyPy
- **Security**: Bandit, secret detection
- **Tests**: Fast unit tests on push

---

## 🐛 Troubleshooting

### Common Issues

#### Tests Failing Locally
```bash
# Clean cache
pytest --cache-clear

# Recreate test database
dropdb test_slidespeaker
createdb test_slidespeaker
```

#### Import Errors
```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt -r requirements-test.txt

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Coverage Not Working
```bash
# Reinstall pytest-cov
pip install --force-reinstall pytest-cov

# Clear .coverage file
rm .coverage
```

#### Slow Tests
```bash
# Run tests in parallel
pytest -n auto

# Skip slow tests
pytest -m "not slow"

# Profile tests
pytest --durations=0
```

### Getting Help

1. Check test logs: `pytest -vv`
2. Enable debugging: `pytest --pdb`
3. Check GitHub Actions logs
4. Ask in team chat

---

## 📚 Best Practices

### DO ✅
- Write tests for new features
- Keep tests fast and isolated
- Use fixtures for common setup
- Mock external services
- Test edge cases and errors
- Follow AAA pattern (Arrange, Act, Assert)

### DON'T ❌
- Test implementation details
- Use real external APIs
- Write flaky tests
- Skip test coverage
- Commit broken tests
- Ignore test failures

---

## 📖 References

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [Testing Best Practices](https://testingjavascript.com/)
- [CI/CD Guide](https://github.com/features/actions)

---

**Need help?** Contact the team or create an issue! 🚀
