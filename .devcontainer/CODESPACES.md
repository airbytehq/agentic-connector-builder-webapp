# Codespaces Quick Start

This project is ready for GitHub Codespaces. Follow these steps to develop and test in your browser:

## 1. Open in Codespaces
- Click "Code" > "Open with Codespaces" on GitHub.

## 2. Wait for Setup
- Dependencies will be installed automatically (`uv sync`).
- Port 3000 will be forwarded for browser preview.

## 3. Run the App
- In the terminal, start the app:
  ```bash
  uv run reflex run
  ```
- Open the browser preview for port 3000.

## 4. Run E2E Tests
- In the terminal, run:
  ```bash
  pytest tests/e2e
  ```

## 5. Playwright Extension
- The Playwright VS Code extension is pre-installed for test authoring and running.

---
For more details, see the main README.
