"""
Money Radar — License Integration Guide

How to integrate the license system into feeds.fun's FastAPI backend.

Step 1: Copy the `license/` directory into feeds.fun's `ffun/` directory.

Step 2: In `ffun/application.py`, add:

    from license import setup_license

    # After app = FastAPI(...)
    setup_license(app)

Step 3: Add LICENSE_SECRET_KEY to .env:

    LICENSE_SECRET_KEY=your-random-secret-here

Step 4: Copy license-page.html to feeds.fun's frontend public directory.

Step 5: Add a route in the frontend that serves the license page
        when no valid license cookie is found.
"""

# This file serves as documentation only.
# The actual integration code is in __init__.py, middleware.py, and routes.py.
