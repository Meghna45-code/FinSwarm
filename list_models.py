import asyncio
import os
import sys

project_root = r"c:\Users\HP\OneDrive\Desktop\FinSwarm"
sys.path.insert(0, project_root)

env_path = os.path.join(project_root, ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip("\"'")

async def main():
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    print("Listing available models:")
    for m in genai.list_models():
        print(f" - {m.name}")

if __name__ == "__main__":
    asyncio.run(main())
