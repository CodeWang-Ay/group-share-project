"""
数据库初始化脚本
独立运行时用于初始化数据库和创建管理员用户
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from database.connection import init_db


def main():
    """
    Main initialization function

    Execute database initialization process:
    1. Check database environment
    2. Initialize database structure
    3. Create admin user
    """
    print("🚀 Starting basic authentication system database initialization...")
    print("-" * 50)

    try:
        # Execute database initialization
        init_db()

        print("-" * 50)
        print("✅ Database initialization successful!")
        print("📋 Database info:")
        print(f"   - Database file: {Path(__file__).parent / 'app.db'}")
        print("   - Default admin: admin/admin")
        print("   - Users table: users")
        print("   - Supported roles: admin, teacher, student")
        print()
        print("🎯 Next steps:")
        print("   1. Install dependencies: pip install -r backend/requirements.txt")
        print("   2. Start service: python backend/main.py")
        print("   3. Access application: http://localhost:8000")

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("Please check error messages and retry")
        sys.exit(1)


if __name__ == "__main__":
    main()