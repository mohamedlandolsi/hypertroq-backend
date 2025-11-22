#!/usr/bin/env python3
"""Setup script for initializing the project."""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """Run a shell command and handle errors."""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    try:
        subprocess.run(command, check=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed: {e}")
        return False


def main():
    """Main setup function."""
    print("\n🚀 HypertroQ Backend Setup")
    print("="*60)
    
    # Check if .env exists
    if not Path(".env").exists():
        print("\n⚠️  Creating .env file from .env.example...")
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ .env file created. Please update it with your configuration.")
        else:
            print("❌ .env.example not found!")
            return
    
    # Install dependencies with Poetry
    if not run_command(
        ["poetry", "install"],
        "Installing Python dependencies with Poetry"
    ):
        print("\n⚠️  Poetry not found. Trying pip install...")
        # Generate requirements.txt from pyproject.toml
        run_command(
            ["poetry", "export", "-f", "requirements.txt", "--output", "requirements.txt", "--without-hashes"],
            "Exporting requirements.txt"
        )
        if Path("requirements.txt").exists():
            run_command(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                "Installing dependencies with pip"
            )
    
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Update .env with your configuration")
    print("2. Start Docker services: docker-compose up -d postgres redis")
    print("3. Run migrations: poetry run alembic upgrade head")
    print("4. Start the application: poetry run uvicorn app.main:app --reload")
    print("\n📚 Documentation: http://localhost:8000/docs")
    print("="*60)


if __name__ == "__main__":
    main()
