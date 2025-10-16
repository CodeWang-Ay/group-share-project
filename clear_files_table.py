#!/usr/bin/env python3
"""
清空files表的数据
此脚本会删除所有文件记录和对应的物理文件
"""

import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "backend"))

from database.connection import get_db

def clear_files_table():
    """清空files表和对应的物理文件"""
    print("准备清空files表...")
    print("警告：此操作不可逆，将删除所有文件记录和物理文件！")

    # 确认操作
    confirm = input("确定要继续吗？(输入 'YES' 确认): ")
    if confirm != 'YES':
        print("操作已取消")
        return False

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 1. 首先获取所有文件的路径，用于删除物理文件
            print("正在获取文件列表...")
            cursor.execute("SELECT id, filename, file_path FROM files")
            files = cursor.fetchall()

            print(f"找到 {len(files)} 个文件记录")

            # 2. 删除物理文件
            deleted_physical_files = 0
            for file_id, filename, file_path in files:
                if file_path and os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_physical_files += 1
                        print(f"已删除物理文件: {filename}")
                    except Exception as e:
                        print(f"删除物理文件失败 {filename}: {str(e)}")
                else:
                    print(f"物理文件不存在: {filename}")

            print(f"\n已删除 {deleted_physical_files} 个物理文件")

            # 3. 清空数据库表
            print("正在清空数据库表...")
            cursor.execute("DELETE FROM files")

            # 重置自增ID
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='files'")

            # 检查结果
            cursor.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]

            print(f"数据库表已清空，剩余记录数: {count}")

            conn.commit()
            return True

    except Exception as e:
        print(f"操作失败: {str(e)}")
        return False

def check_table_status():
    """检查表状态"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files'")
            table_exists = cursor.fetchone()

            if not table_exists:
                print("files表不存在")
                return False

            # 检查记录数
            cursor.execute("SELECT COUNT(*) FROM files")
            count = cursor.fetchone()[0]

            print(f"当前files表状态:")
            print(f"   - 表存在: 是")
            print(f"   - 记录数: {count}")

            if count > 0:
                cursor.execute("SELECT id, filename, file_size FROM files LIMIT 5")
                samples = cursor.fetchall()
                print(f"   - 示例记录:")
                for record in samples:
                    file_id, filename, file_size = record
                    size_str = f"{file_size/1024/1024:.2f}MB" if file_size > 1024*1024 else f"{file_size/1024:.2f}KB"
                    print(f"     * ID:{file_id}, {filename} ({size_str})")

            return True

    except Exception as e:
        print(f"检查表状态失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("清空files表工具")
    print("=" * 60)

    # 检查当前状态
    print("\n1. 检查当前表状态:")
    check_table_status()

    # 执行清空操作
    print("\n2. 执行清空操作:")
    success = clear_files_table()

    # 检查最终状态
    print("\n3. 检查最终状态:")
    check_table_status()

    if success:
        print("\n操作完成！files表已清空")
    else:
        print("\n操作失败！")

if __name__ == "__main__":
    main()