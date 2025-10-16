#!/usr/bin/env python3
"""
文件上传测试脚本
用于调试文件上传时数据库不插入记录的问题
"""

import os
import sys
import sqlite3
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

from services.file_service import FileService
from database.connection import get_db, DATABASE_PATH

def test_database_connection():
    """测试数据库连接和插入操作"""
    print("🔍 测试数据库连接...")

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 测试查询
            cursor.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]
            print(f"✅ 数据库连接成功，当前文件数量: {count}")

            # 测试手动插入
            print("🧪 测试手动插入操作...")
            cursor.execute("""
                INSERT INTO files (
                    filename, file_path, file_size, file_type, file_hash,
                    uploader_id, description, tags, is_public
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "test_file.txt",
                "/test/path/test_file.txt",
                1024,
                "text/plain",
                "test_hash_123",
                1,
                "Test file description",
                "test",
                0
            ))

            # 检查是否插入成功（在with块内）
            cursor.execute("SELECT COUNT(*) FROM files")
            new_count = cursor.fetchone()[0]
            print(f"📊 在with块内插入后文件数量: {new_count}")

            # 获取刚插入的记录ID
            cursor.execute("SELECT last_insert_rowid()")
            insert_id = cursor.fetchone()[0]
            print(f"🆔 插入的记录ID: {insert_id}")

        # with块结束后，检查是否提交
        print("\n🔍 检查事务是否自动提交...")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM files")
            final_count = cursor.fetchone()[0]
            print(f"📊 事务结束后文件数量: {final_count}")

            # 查询刚插入的记录
            cursor.execute("SELECT filename FROM files WHERE id = ?", (insert_id,))
            result = cursor.fetchone()
            if result:
                print(f"✅ 找到插入的记录: {result[0]}")
            else:
                print("❌ 没有找到插入的记录，事务可能没有提交")

            # 清理测试数据
            cursor.execute("DELETE FROM files WHERE id = ?", (insert_id,))
            print(f"🧹 清理测试数据，删除记录: {insert_id}")

    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        return False

    return True

def test_file_service_upload():
    """测试FileService.upload_file方法"""
    print("\n🔍 测试FileService.upload_file方法...")

    # 创建测试文件数据
    test_content = b"This is a test file content for debugging upload issue."
    test_filename = "debug_test_file.txt"

    try:
        # 调用FileService.upload_file
        file_obj, error = FileService.upload_file(
            file_data=test_content,
            original_filename=test_filename,
            uploader_id=1,
            description="Debug test file",
            tags="debug,test",
            is_public=False
        )

        if error:
            print(f"❌ 文件上传失败: {error}")
            return False

        if file_obj:
            print(f"✅ 文件上传成功:")
            print(f"   - ID: {file_obj.id}")
            print(f"   - 文件名: {file_obj.filename}")
            print(f"   - 路径: {file_obj.file_path}")
            print(f"   - 大小: {file_obj.file_size}")

            # 验证文件是否确实保存到数据库
            print("\n🔍 验证数据库中的记录...")
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM files WHERE id = ?", (file_obj.id,))
                record = cursor.fetchone()

                if record:
                    print("✅ 数据库中找到记录:")
                    print(f"   - 文件名: {record[1]}")
                    print(f"   - 上传者ID: {record[6]}")
                    print(f"   - 描述: {record[8]}")
                else:
                    print("❌ 数据库中没有找到记录！")
                    return False

                # 清理测试数据
                cursor.execute("DELETE FROM files WHERE id = ?", (file_obj.id,))
                print(f"🧹 清理测试数据")

                # 删除文件
                if os.path.exists(file_obj.file_path):
                    os.remove(file_obj.file_path)
                    print(f"🗑️ 删除测试文件: {file_obj.file_path}")

            return True
        else:
            print("❌ 文件上传返回None，没有错误信息")
            return False

    except Exception as e:
        print(f"❌ FileService测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("🚀 开始文件上传调试测试...")
    print("=" * 50)

    # 检查数据库文件
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ 数据库文件不存在: {DATABASE_PATH}")
        return

    print(f"📁 数据库文件路径: {DATABASE_PATH}")
    print(f"📁 上传目录路径: {FileService.UPLOAD_DIR}")

    # 测试1: 数据库连接
    if not test_database_connection():
        print("\n❌ 数据库连接测试失败，停止测试")
        return

    # 测试2: FileService上传
    if not test_file_service_upload():
        print("\n❌ FileService上传测试失败")
        return

    print("\n✅ 所有测试通过！")

if __name__ == "__main__":
    main()