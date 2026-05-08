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
                minutes TEXT,
                status VARCHAR(20) DEFAULT 'scheduled',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
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
                material_status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_presenters_meeting ON meeting_presenters(meeting_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_presenters_user ON meeting_presenters(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_presenters_material_status ON meeting_presenters(material_status)")

        # 创建组会材料关联表（独立存储汇报材料，不依赖 files 表）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meeting_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                file_id INTEGER,
                presenter_id INTEGER,
                filename VARCHAR(255),
                file_path VARCHAR(500),
                file_size INTEGER,
                file_type VARCHAR(100),
                uploaded_by INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (meeting_id) REFERENCES meetings(id) ON DELETE CASCADE,
                FOREIGN KEY (presenter_id) REFERENCES meeting_presenters(id) ON DELETE CASCADE,
                FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_files_meeting ON meeting_files(meeting_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meeting_files_presenter ON meeting_files(presenter_id)")

        # 创建研究任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                priority VARCHAR(20) DEFAULT 'middle',
                status VARCHAR(20) DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                assignee_id INTEGER NOT NULL,
                creator_id INTEGER NOT NULL,
                task_type VARCHAR(20) DEFAULT 'personal',
                deadline TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (creator_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON research_tasks(assignee_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_creator ON research_tasks(creator_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON research_tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON research_tasks(deadline)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_type ON research_tasks(task_type)")

        # 创建文献表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                journal TEXT,
                doi TEXT,
                abstract TEXT,
                pdf_path TEXT,
                pdf_size INTEGER,
                file_hash TEXT,
                arxiv_link TEXT,
                semantic_scholar_link TEXT,
                download_count INTEGER DEFAULT 0,
                uploader_id INTEGER NOT NULL,
                team_library INTEGER DEFAULT 1,
                is_deleted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_hash ON papers(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_uploader ON papers(uploader_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year)")
        # team_library 和 is_deleted 索引在迁移后创建

        # 创建标签表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                tag_type TEXT DEFAULT 'system',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_name ON tags(name)")

        # 创建个人文献表（物理隔离）- 先创建，因为 paper_user_relations 有外键引用
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personal_papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT,
                year INTEGER,
                journal TEXT,
                doi TEXT,
                abstract TEXT,
                pdf_path TEXT,
                pdf_size INTEGER,
                file_hash TEXT,
                arxiv_link TEXT,
                semantic_scholar_link TEXT,
                download_count INTEGER DEFAULT 0,
                owner_user_id INTEGER NOT NULL,
                source_type TEXT DEFAULT 'uploaded',
                source_paper_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (source_paper_id) REFERENCES papers(id) ON DELETE SET NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_papers_hash ON personal_papers(file_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_papers_owner ON personal_papers(owner_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_papers_doi ON personal_papers(doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_papers_year ON personal_papers(year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_personal_papers_source ON personal_papers(source_paper_id)")

        # 创建文献-用户关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_user_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id INTEGER,                    -- 允许 NULL（个人文献不需要）
                user_id INTEGER NOT NULL,
                read_status TEXT DEFAULT 'unread',
                is_starred INTEGER DEFAULT 0,
                library_type TEXT DEFAULT 'public',
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_viewed_at TIMESTAMP,
                personal_paper_id INTEGER,           -- 个人文献关联
                relation_type TEXT DEFAULT 'team_view',
                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (personal_paper_id) REFERENCES personal_papers(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_user_paper ON paper_user_relations(paper_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_user_user ON paper_user_relations(user_id)")
        # 唯一索引：团队文献用 (paper_id, user_id)，个人文献用 (personal_paper_id, user_id)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_paper_user_unique ON paper_user_relations(paper_id, user_id) WHERE paper_id IS NOT NULL")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_personal_user_unique ON paper_user_relations(personal_paper_id, user_id) WHERE personal_paper_id IS NOT NULL")
        # personal_paper_id 索引在迁移后创建

        # 创建文献-标签关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_tags (
                paper_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (paper_id, tag_id),
                FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)

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

        # === 研究进展相关表 ===
        # 创建研究进展表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                research_direction TEXT NOT NULL,
                weekly_progress TEXT NOT NULL,
                next_goal TEXT NOT NULL,
                difficulties TEXT,
                completion_rate INTEGER DEFAULT 0,
                attachments TEXT,
                submission_period TEXT DEFAULT 'weekly',
                submission_date DATETIME,
                period_start DATETIME,
                period_end DATETIME,
                status TEXT DEFAULT 'normal',
                supervisor_feedback TEXT,
                feedback_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_user ON research_progress(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_status ON research_progress(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress_submission ON research_progress(submission_date)")

        # 创建提交周期设置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS progress_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                period_type TEXT DEFAULT 'weekly',
                reminder_enabled INTEGER DEFAULT 1,
                reminder_days INTEGER DEFAULT 1,
                next_deadline DATETIME,
                created_by INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_user ON progress_settings(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_settings_deadline ON progress_settings(next_deadline)")

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

        # 初始化系统标签
        system_tags = ['Transformer', 'BERT', 'CNN', '大模型', 'NLP', '计算机视觉']
        cursor.execute("SELECT COUNT(*) FROM tags WHERE tag_type = 'system'")
        if cursor.fetchone()[0] == 0:
            for tag_name in system_tags:
                cursor.execute(
                    "INSERT INTO tags (name, tag_type) VALUES (?, ?)",
                    (tag_name, 'system')
                )
            print(f"✅ 已创建 {len(system_tags)} 个系统标签")

        # === 数据迁移：为已存在的表添加新字段 ===
        # 检查 papers 表是否有 team_library 列
        cursor.execute("PRAGMA table_info(papers)")
        papers_columns = [col[1] for col in cursor.fetchall()]
        if 'team_library' not in papers_columns:
            cursor.execute("ALTER TABLE papers ADD COLUMN team_library INTEGER DEFAULT 1")
            print("✅ 已为 papers 表添加 team_library 列")
        if 'is_deleted' not in papers_columns:
            cursor.execute("ALTER TABLE papers ADD COLUMN is_deleted INTEGER DEFAULT 0")
            print("✅ 已为 papers 表添加 is_deleted 列")

        # 检查 paper_user_relations 表的 paper_id 是否有 NOT NULL 约束
        cursor.execute("PRAGMA table_info(paper_user_relations)")
        relations_info = cursor.fetchall()
        relations_columns = {col[1]: col[3] for col in relations_info}  # col[3] 是 notnull 标志

        # 如果 paper_id 有 NOT NULL 约束（col[3]=1），需要重建表
        if relations_columns.get('paper_id', 0) == 1:
            # 重建 paper_user_relations 表，移除 paper_id 的 NOT NULL 约束
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paper_user_relations_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER,
                    user_id INTEGER NOT NULL,
                    read_status TEXT DEFAULT 'unread',
                    is_starred INTEGER DEFAULT 0,
                    library_type TEXT DEFAULT 'public',
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_viewed_at TIMESTAMP,
                    personal_paper_id INTEGER,
                    relation_type TEXT DEFAULT 'team_view',
                    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (personal_paper_id) REFERENCES personal_papers(id) ON DELETE CASCADE
                )
            """)
            # 复制数据
            cursor.execute("""
                INSERT INTO paper_user_relations_new
                SELECT id, paper_id, user_id, read_status, is_starred, library_type, added_at, last_viewed_at,
                       personal_paper_id, relation_type
                FROM paper_user_relations
            """)
            # 删除旧表
            cursor.execute("DROP TABLE paper_user_relations")
            # 重命名新表
            cursor.execute("ALTER TABLE paper_user_relations_new RENAME TO paper_user_relations")
            print("✅ 已重建 paper_user_relations 表，移除 paper_id 的 NOT NULL 约束")

        # 检查是否缺少新列
        cursor.execute("PRAGMA table_info(paper_user_relations)")
        relations_columns = [col[1] for col in cursor.fetchall()]
        if 'personal_paper_id' not in relations_columns:
            cursor.execute("ALTER TABLE paper_user_relations ADD COLUMN personal_paper_id INTEGER")
            print("✅ 已为 paper_user_relations 表添加 personal_paper_id 列")
        if 'relation_type' not in relations_columns:
            cursor.execute("ALTER TABLE paper_user_relations ADD COLUMN relation_type TEXT DEFAULT 'team_view'")
            print("✅ 已为 paper_user_relations 表添加 relation_type 列")

        # 迁移现有数据：标记为团队文献和团队视图
        cursor.execute("UPDATE papers SET team_library = 1 WHERE team_library IS NULL")
        cursor.execute("UPDATE paper_user_relations SET relation_type = 'team_view' WHERE relation_type IS NULL")

        # 创建新字段的索引（迁移后）
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_team_library ON papers(team_library)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_doi ON papers(doi)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_deleted ON papers(is_deleted)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_user_personal ON paper_user_relations(personal_paper_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_user_paper ON paper_user_relations(paper_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_user_user ON paper_user_relations(user_id)")
        # 唯一索引：分开处理团队和个人文献
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_paper_user_unique ON paper_user_relations(paper_id, user_id) WHERE paper_id IS NOT NULL")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_personal_user_unique ON paper_user_relations(personal_paper_id, user_id) WHERE personal_paper_id IS NOT NULL")
        print("✅ 已完成现有数据迁移")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_papers_deleted ON papers(is_deleted)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_user_personal ON paper_user_relations(personal_paper_id)")
        print("✅ 已完成现有数据迁移")


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