# Stock Dashboard Update

## Recent Changes (2026-02-11)
- **Immediate Data Reflection**: Adding a ticker now fetches and displays data instantly.
- **Company Names**: Ticker symbols now show their company name (e.g., `9997.T (BELLUNA CO)`).

## Upgrade Instructions
Since the database schema has changed (added `name` column), please restart the application to apply changes:
1. Close all open command prompt windows and the browser page.
2. Run `start_dashboard.bat` again.

## Usage
- **Add Ticker**: Enter symbol (e.g., `7203.T`) in the sidebar and click Add.
- **Remove Ticker**: Select from the dropdown and click Remove.
