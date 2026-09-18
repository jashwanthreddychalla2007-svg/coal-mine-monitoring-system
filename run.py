import os

import uvicorn


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")

    print("=" * 60)
    print(" [*] Starting KhananRakshak / CoalGuard AI Platform")
    print(f" [>] Dashboard URL: http://{host}:{port}")
    print(f" [>] Interactive Swagger Docs: http://{host}:{port}/docs")
    print("=" * 60)

    uvicorn.run("backend.main:app", host=host, port=port)
