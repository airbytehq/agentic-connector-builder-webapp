"""Entry point for the Agentic Connector Builder WebApp."""

from agentic_connector_builder_webapp.agentic_connector_builder_webapp import app

# Vercel expects the app to be named 'app'
application = app


def main():
    """Main function for local development."""
    print("Hello from agentic-connector-builder-webapp!")
    print("For local development, use: reflex run")
    print("For production deployment, this app is configured for Vercel.")


if __name__ == "__main__":
    main()
