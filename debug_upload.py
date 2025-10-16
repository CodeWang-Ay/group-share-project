#!/usr/bin/env python3
"""
调试文件上传问题的脚本
专门用于排查数据库插入失败的原因
"""

import os
import sys
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

from services.file_service import FileService
from database.connection import get_db

def debug_upload_process():
    """详细调试文件上传过程"""
    print("🔍 开始详细调试文件上传过程...")

    # 创建测试文件数据
    test_content = b"Debug test content - " + b"X" * 100  # 100字节的测试内容
    test_filename = "debug_file.txt"

    print(f"📁 测试文件: {test_filename}")
    print(f"📏 文件大小: {len(test_content)} 字节")

    try:
        # 手动执行FileService.upload_file的步骤，添加调试信息
        print("\n步骤1: 检查文件大小和类型")
        if len(test_content) > FileService.MAX_FILE_SIZE:
            print(f"❌ 文件太大: {len(test_content)} > {FileService.MAX_FILE_SIZE}")
            return
        if not FileService.is_allowed_file(test_filename):
            print(f"❌ 不支持的文件类型: {test_filename}")
            return
        print("✅ 文件大小和类型检查通过")

        print("\n步骤2: 检查重复文件名")
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, filename FROM files
                WHERE filename = ? AND uploader_id = ? AND status = 'active'
            """, (test_filename, 1))

            existing_file = cursor.fetchone()
            if existing_file:
                print(f"❌ 文件名已存在: {existing_file}")
                return
            print("✅ 没有重复文件名")

        print("\n步骤3: 保存文件到磁盘")
        FileService.init_upload_directory()
        unique_filename = FileService.generate_unique_filename(test_filename)
        file_path = FileService.UPLOAD_DIR / unique_filename

        print(f"📁 唯一文件名: {unique_filename}")
        print(f"📍 文件路径: {file_path}")

        with open(file_path, 'wb') as f:
            f.write(test_content)
        print("✅ 文件已保存到磁盘")

        print("\n步骤4: 计算文件信息")
        file_size = len(test_content)
        from models.file import File
        file_hash = File.calculate_file_hash(str(file_path))
        file_type = File.get_mime_type(test_filename)

        print(f"📊 文件大小: {file_size}")
        print(f"🔑 文件哈希: {file_hash}")
        print(f"📄 文件类型: {file_type}")

        print("\n步骤5: 检查重复文件内容")
        if file_hash:
            print("🔍 检查是否有相同内容的文件...")
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, filename FROM files
                    WHERE file_hash = ? AND uploader_id = ? AND status = 'active'
                """, (file_hash, 1))

                duplicate_content = cursor.fetchone()
                if duplicate_content:
                    print(f"❌ 发现重复内容: {duplicate_content}")
                    # 删除刚创建的文件
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print("🗑️ 已删除重复文件")
                    return
                print("✅ 没有重复内容")

        print("\n步骤6: 创建文件对象")
        file_obj = File(
            filename=test_filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_type,
            uploader_id=1,
            file_hash=file_hash,
            description="Debug test file",
            tags="debug",
            is_public=False
        )
        print(f"✅ 文件对象创建成功，ID: {file_obj.id}")

        print("\n步骤7: 插入数据库记录")
        try:
            with get_db() as conn:
                cursor = conn.cursor()

                print("🔍 执行INSERT语句...")
                cursor.execute("""
                    INSERT INTO files (
                        filename, file_path, file_size, file_type, file_hash,
                        uploader_id, description, tags, is_public
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    file_obj.filename,
                    file_obj.file_path,
                    file_obj.file_size,
                    file_obj.file_type,
                    file_obj.file_hash,
                    file_obj.uploader_id,
                    file_obj.description,
                    file_obj.tags,
                    file_obj.is_public
                ))
                print("✅ INSERT语句执行成功")

                print("🔍 获取last_insert_rowid()...")
                cursor.execute("SELECT last_insert_rowid()")
                insert_id = cursor.fetchone()[0]
                print(f"✅ 获取到插入ID: {insert_id}")

                file_obj.id = insert_id

                # 在同一个连接中验证插入
                print("🔍 在当前连接中验证插入...")
                cursor.execute("SELECT COUNT(*) FROM files WHERE id = ?", (insert_id,))
                count_in_connection = cursor.fetchone()[0]
                print(f"📊 当前连接中的记录数: {count_in_connection}")

        except Exception as e:
            print(f"❌ 数据库插入失败: {e}")
            import traceback
            traceback.print_exc()
            # 清理文件
            if os.path.exists(file_path):
                os.remove(file_path)
            return

        print("\n步骤8: 验证最终结果")
        # 使用新连接验证
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE id = ?", (file_obj.id,))
            final_record = cursor.fetchone()

            if final_record:
                print("✅ 数据库中找到记录!")
                print(f"   - ID: {final_record[0]}")
                print(f"   - 文件名: {final_record[1]}")
                print(f"   - 描述: {final_record[8]}")

                # 清理测试数据
                cursor.execute("DELETE FROM files WHERE id = ?", (file_obj.id,))
                print(f"🧹 清理测试数据")
            else:
                print("❌ 数据库中没有找到记录！")
                print("这表明事务没有正确提交")

        # 清理文件
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ 删除测试文件")

    except Exception as e:
        print(f"❌ 调试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_upload_process()