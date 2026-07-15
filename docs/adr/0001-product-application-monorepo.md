# Keep the product application in this repository

This repository owns the tutoring-platform frontend, backend, local end-to-end harness,
and product documentation. The Gauntlet ledger remains a separate accountability
boundary so product implementation cannot silently alter its own grading machinery;
keeping both application layers together also gives the repository-local Playwright
harness one clean-checkout contract.
