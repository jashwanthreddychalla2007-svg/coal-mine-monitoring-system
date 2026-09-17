import uvicorn

if __name__ == "__main__":
    print("=" * 60)
    print(" ⛏️  Starting KhananRakshak / CoalGuard AI Platform")
    print(" 🌐  Dashboard URL: http://localhost:8000")
    print(" 📖  Interactive Swagger Docs: http://localhost:8000/docs")
    print("=" * 60)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
