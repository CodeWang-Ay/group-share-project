"""
数据库连接和初始化模块
提供SQLite数据库连接和初始化功能
"""

import sqlite3
import os
from contextlib import contextmanager
from typing import Generator
from pathlib import Path

# 数据库文件路径
DATABASE_PATH = Path(__file__).parent / "app.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"


def get_db() -> sqlite3.Connection:
    """
    获取数据库连接

    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
    return conn


@contextmanager
def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """
    获取数据库游标的上下文管理器

    Yields:
        sqlite3.Cursor: 数据库游标对象
    """
    conn = get_db()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    初始化数据库，创建用户表、文件表和预设管理员账号

    该函数会：
    1. 创建users表
    2. 创建files表
    3. 创建预设管理员用户admin/admin
    """
    # 确保数据库目录存在
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_db_cursor() as cursor:
        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL,
                email VARCHAR(100),
                phone VARCHAR(20),
                student_id VARCHAR(50),
                research_direction VARCHAR(200),
                status VARCHAR(20) DEFAULT 'active',
                graduation_status VARCHAR(50),
                supervisor VARCHAR(100),
                degree_type VARCHAR(50),
                work_location VARCHAR(100),
                work_company VARCHAR(100),
                personal_bio TEXT,
                personal_homepage VARCHAR(200),
                gender VARCHAR(10),
                id_card VARCHAR(20),
                bank_card VARCHAR(30),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建username字段的唯一索引
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_username ON users(username)")

        # 创建组会表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                meeting_type VARCHAR(50) DEFAULT 'regular',
                description TEXT,
                location VARCHAR(100),
                is_online BOOLEAN DEFAULT 0,
                online_link VARCHAR(500),
                scheduled_at TIMESTAMP NOT NULL,
                duration_total INTEGER DEFAULT 60,
                material_required BOOLEAN DEFAULT 1,
                material_deadline TIMESTAMP,
                notes TEXT,
                status VARCHAR(20) DEFAULT 'scheduled',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_scheduled ON meetings(scheduled_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meetings_created_by ON meetings(created_by)")

        # 创建汇报人关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meeting_presenters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                presenter_type VARCHAR(20) DEFAULT 'pending',
                duration_minutes INTEGER DEFAULT 20,
                material_required BOOLEAN DEFAULT 1,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_presenters_meeting ON meeting_presenters(meeting_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_presenters_user ON meeting_presenters(user_id)")

        # 创建组会材料关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meeting_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                presenter_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE,
                FOREIGN KEY (presenter_id) REFERENCES meeting_presenters(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_files_meeting ON meeting_files(meeting_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_files_file ON meeting_files(file_id)")

        # 创建文件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size INTEGER NOT NULL,
                file_type VARCHAR(100) NOT NULL,
                file_hash VARCHAR(64) UNIQUE,
                uploader_id INTEGER NOT NULL,
                upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                tags TEXT,
                is_public BOOLEAN DEFAULT 0,
                download_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 创建文件表的索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_uploader ON files(uploader_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_status ON files(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_upload_time ON files(upload_time)")

        # 检查是否已存在admin用户
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()

        if not admin_exists:
            # 导入bcrypt用于密码哈希
            import bcrypt

            # 创建admin用户的密码哈希（密码为"admin"）
            password = "admin"
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # 插入预设管理员用户
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", password_hash.decode('utf-8'), "admin")
            )
            print("✅ 预设管理员用户admin/admin已创建")
        else:
            print("ℹ️ 管理员用户已存在，跳过创建")


def close_db() -> None:
    """
    关闭数据库连接（用于清理资源）
    """
    # SQLite连接会自动关闭，这里主要是为了接口完整性
    pass


# 数据库初始化检查
if __name__ == "__main__":
    print("正在初始化数据库...")
    init_db()
    print("数据库初始化完成！")