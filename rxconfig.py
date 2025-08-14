import reflex as rx

config = rx.Config(
    app_name="agentic_connector_builder_webapp",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ],
)