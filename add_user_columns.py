#!/usr/bin/env python3
"""
为user表添加新列的脚本
"""

import sqlite3
import os
from pathlib import Path

# 数据库文件路径
DB_PATH = Path(__file__).parent / "backend" / "database" / "app.db"

def add_user_columns():
    """
    为users表添加新列并更新现有数据
    """
    if not DB_PATH.exists():
        print(f"数据库文件不存在: {DB_PATH}")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 检查表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"当前users表的列: {columns}")

        # 添加新列（如果不存在）
        new_columns = {
            'email': 'VARCHAR(100)',
            'phone': 'VARCHAR(20)',
            'student_id': 'VARCHAR(50)',
            'research_direction': 'VARCHAR(200)',
            'status': 'VARCHAR(20) DEFAULT "active"'
        }

        for column_name, column_type in new_columns.items():
            if column_name not in columns:
                print(f"添加列: {column_name}")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
            else:
                print(f"列 {column_name} 已存在，跳过")

        # 查看现有用户
        cursor.execute("SELECT id, username, role FROM users")
        users = cursor.fetchall()
        print(f"找到 {len(users)} 个现有用户")

        # 为每个用户更新默认数据
        for user_id, username, role in users:
            print(f"更新用户 {username} (ID: {user_id})")

            # 生成默认值
            default_email = f"{username}@qq.com"
            default_phone = "13800138000"
            default_student_id = f"202{str(user_id).zfill(3)}" if role == "student" else f"T{str(user_id).zfill(3)}"
            default_research = "未设置研究方向"

            # 检查是否已有数据，如果没有则更新
            cursor.execute("SELECT email, phone, student_id, research_direction, status FROM users WHERE id = ?", (user_id,))
            current_data = cursor.fetchone()

            if current_data:
                current_email, current_phone, current_student_id, current_research, current_status = current_data

                # 只更新空值
                update_data = {}
                if not current_email:
                    update_data['email'] = default_email
                if not current_phone:
                    update_data['phone'] = default_phone
                if not current_student_id:
                    update_data['student_id'] = default_student_id
                if not current_research:
                    update_data['research_direction'] = default_research
                if not current_status:
                    update_data['status'] = 'active'

                if update_data:
                    set_clause = ", ".join([f"{k} = ?" for k in update_data.keys()])
                    values = list(update_data.values()) + [user_id]
                    cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
                    print(f"  更新了: {', '.join(update_data.keys())}")
                else:
                    print(f"  用户数据已完整，无需更新")
            else:
                # 插入完整数据（理论上不应该发生）
                cursor.execute("""
                    UPDATE users SET
                    email = ?,
                    phone = ?,
                    student_id = ?,
                    research_direction = ?,
                    status = ?
                    WHERE id = ?
                """, (default_email, default_phone, default_student_id, default_research, 'active', user_id))
                print(f"  完整更新用户数据")

        # 提交更改
        conn.commit()

        # 验证结果
        cursor.execute("SELECT id, username, email, phone, student_id, research_direction, status FROM users")
        updated_users = cursor.fetchall()

        print("\n更新后的用户数据:")
        print("ID\t用户名\t邮箱\t\t\t手机号\t\t学号\t\t研究方向\t\t状态")
        print("-" * 80)
        for user in updated_users:
            print(f"{user[0]}\t{user[1]}\t{user[2]}\t{user[3]}\t{user[4]}\t{user[5]}\t{user[6]}")

        print(f"\n成功更新了 {len(updated_users)} 个用户")

        conn.close()
        return True

    except Exception as e:
        print(f"错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始为users表添加新列并更新数据...")
    success = add_user_columns()
    if success:
        print("操作完成！")
    else:
        print("操作失败！")