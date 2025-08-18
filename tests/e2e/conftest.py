"""Playwright configuration and fixtures for end-to-end tests."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def browser() -> AsyncGenerator[Browser, None]:
    """Create a browser instance for the test session."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        yield browser
        await browser.close()


@pytest.fixture(scope="function")
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """Create a new browser context for each test."""
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
    )
    yield context
    await context.close()


@pytest.fixture(scope="function")
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """Create a new page for each test."""
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for the application during testing."""
    return "http://localhost:3000"


@pytest.fixture(scope="function")
async def app_page(page: Page, base_url: str) -> Page:
    """Navigate to the main application page."""
    await page.goto(base_url)
    await page.wait_for_load_state("networkidle")
    return page


@pytest.fixture
def sample_yaml_for_e2e() -> str:
    """Sample YAML content for e2e testing."""
    return """# E2E Test YAML
name: e2e-test-connector
version: "2.0.0"
description: "End-to-end test connector"

source:
  type: file
  path: "/data/input.json"
destination:
  type: api
  endpoint: "https://api.test.com/data"
transformations:
  - type: json_to_yaml
  - type: validation
    rules:
      - required_fields: ["id", "name"]
"""


@pytest.fixture
def complex_yaml_for_e2e() -> str:
    """Complex YAML content for advanced e2e testing."""
    return """# Complex E2E Test Configuration
name: complex-e2e-connector
version: "3.0.0"
description: "Complex connector for comprehensive testing"

metadata:
  author: "E2E Test Suite"
  created: "2024-01-01"
  tags: ["test", "e2e", "complex"]

source:
  type: database
  connection:
    host: "db.test.com"
    port: 5432
    database: "test_db"
    username: "test_user"
    password: "${DB_PASSWORD}"
  query: |
    SELECT id, name, email, created_at
    FROM users
    WHERE active = true
    ORDER BY created_at DESC
    LIMIT 1000

destination:
  type: webhook
  url: "https://webhook.test.com/data"
  headers:
    Content-Type: "application/json"
    Authorization: "Bearer ${API_TOKEN}"
  batch_size: 100
  retry_config:
    max_retries: 3
    backoff_factor: 2

transformations:
  - type: field_mapping
    mappings:
      user_id: id
      full_name: name
      email_address: email
      registration_date: created_at
  - type: data_validation
    rules:
      - field: email_address
        type: email
        required: true
      - field: registration_date
        type: datetime
        format: "ISO8601"
  - type: enrichment
    source: "user_profiles"
    join_key: "user_id"
    fields: ["profile_data", "preferences"]

monitoring:
  enabled: true
  metrics:
    - "records_processed"
    - "processing_time"
    - "error_rate"
  alerts:
    - condition: "error_rate > 0.05"
      action: "email"
      recipients: ["admin@test.com"]
"""


# Configure pytest for async tests
def pytest_configure(config):
    """Configure pytest for Playwright e2e tests."""
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow_e2e: mark test as a slow end-to-end test")
    config.addinivalue_line(
        "markers", "browser: mark test as requiring browser automation"
    )
