"""Playwright configuration for end-to-end testing."""

import os


def pytest_playwright_config(config):
    """Configure Playwright for pytest integration."""
    return {
        "browser_name": "chromium",
        "headless": True,
        "slow_mo": 0,
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
        "ignore_https_errors": True,
        "viewport": {"width": 1280, "height": 720},
        "video": "retain-on-failure",
        "screenshot": "only-on-failure",
        "trace": "retain-on-failure",
    }


# Playwright configuration for direct usage (non-pytest)
PLAYWRIGHT_CONFIG = {
    "browsers": ["chromium"],
    "headless": True,
    "viewport": {"width": 1280, "height": 720},
    "ignore_https_errors": True,
    "video": {"mode": "retain-on-failure", "size": {"width": 1280, "height": 720}},
    "screenshot": {"mode": "only-on-failure", "full_page": True},
    "trace": {
        "mode": "retain-on-failure",
        "screenshots": True,
        "snapshots": True,
        "sources": True,
    },
    "test_dir": "tests/e2e",
    "timeout": 30000,  # 30 seconds
    "expect_timeout": 5000,  # 5 seconds
    "navigation_timeout": 30000,  # 30 seconds
    "action_timeout": 10000,  # 10 seconds
    "base_url": "http://localhost:3000",
    "workers": 1,  # Run tests sequentially for stability
    "retry": 2,  # Retry failed tests twice
    "reporter": [
        ["html", {"open": "never", "outputFolder": "test-results/html-report"}],
        ["json", {"outputFile": "test-results/results.json"}],
        ["junit", {"outputFile": "test-results/junit.xml"}],
        ["line"],
    ],
    "output_dir": "test-results",
    "preserve_output": "failures-only",
    "use": {
        "browser_name": "chromium",
        "channel": None,
        "headless": True,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
        "java_script_enabled": True,
        "bypass_csp": False,
        "user_agent": None,
        "device_scale_factor": 1,
        "is_mobile": False,
        "has_touch": False,
        "color_scheme": "dark",
        "reduced_motion": "reduce",
        "forced_colors": None,
        "accept_downloads": True,
        "trace": "retain-on-failure",
        "video": "retain-on-failure",
        "screenshot": "only-on-failure",
    },
    "projects": [
        {"name": "chromium", "use": {"browser_name": "chromium"}},
        {"name": "firefox", "use": {"browser_name": "firefox"}},
        {"name": "webkit", "use": {"browser_name": "webkit"}},
    ],
    "web_server": {
        "command": "uv run reflex run --env dev",
        "port": 3000,
        "timeout": 120000,  # 2 minutes to start
        "reuseExistingServer": True,
        "stdout": "pipe",
        "stderr": "pipe",
        "env": {"NODE_ENV": "test", "REFLEX_ENV": "test"},
    },
}


def get_browser_config(browser_name: str = "chromium") -> dict:
    """Get browser-specific configuration."""
    base_config = {
        "headless": os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true",
        "slow_mo": int(os.getenv("PLAYWRIGHT_SLOW_MO", "0")),
        "timeout": int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000")),
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }

    browser_configs = {
        "chromium": {
            **base_config,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
            ],
        },
        "firefox": {
            **base_config,
            "firefox_user_prefs": {
                "security.tls.insecure_fallback_hosts": "localhost",
                "network.stricttransportsecurity.preloadlist": False,
            },
        },
        "webkit": {**base_config, "ignore_default_args": ["--enable-automation"]},
    }

    return browser_configs.get(browser_name, browser_configs["chromium"])


def get_test_environment_config() -> dict:
    """Get test environment specific configuration."""
    env = os.getenv("TEST_ENV", "local")

    configs = {
        "local": {
            "base_url": "http://localhost:3000",
            "timeout": 30000,
            "workers": 1,
            "retry": 2,
        },
        "ci": {
            "base_url": "http://localhost:3000",
            "timeout": 60000,
            "workers": 2,
            "retry": 3,
            "headless": True,
        },
        "staging": {
            "base_url": os.getenv("STAGING_URL", "https://staging.example.com"),
            "timeout": 45000,
            "workers": 2,
            "retry": 1,
        },
    }

    return configs.get(env, configs["local"])


# Export main configuration
__all__ = [
    "PLAYWRIGHT_CONFIG",
    "pytest_playwright_config",
    "get_browser_config",
    "get_test_environment_config",
]
