"""
Production server using Waitress (Windows-compatible WSGI server)
"""
from waitress import serve
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))

    print(f"Starting production server on {host}:{port}")
    print("Press Ctrl+C to stop")

    # Waitress - production-ready WSGI server for Windows
    serve(
        app,
        host=host,
        port=port,
        threads=8,  # Количество потоков
        channel_timeout=60,
        cleanup_interval=30,
        _quiet=False
    )
