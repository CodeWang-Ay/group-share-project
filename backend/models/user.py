"""
用户数据模型
定义User类和相关的数据库操作
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import bcrypt


@dataclass
class User:
    """
    用户数据模型

    属性:
        id: 用户ID（数据库自增）
        username: 用户名（唯一）
        password_hash: 密码哈希值
        role: 用户角色（admin/teacher/student）
        email: 邮箱
        phone: 电话
        student_id: 学号
        research_direction: 研究方向
        status: 状态
        avatar: 用户头像URL
        created_at: 创建时间
        updated_at: 更新时间
    """
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    role: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    student_id: Optional[str] = None
    research_direction: Optional[str] = None
    status: Optional[str] = None
    avatar: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """
        初始化后处理，验证数据有效性
        """
        if not self.username:
            raise ValueError("用户名不能为空")

        if not self.password_hash:
            raise ValueError("密码哈希不能为空")

        if self.role not in ["admin", "teacher", "student"]:
            raise ValueError("角色必须是admin、teacher或student之一")

    @classmethod
    def create_user(cls, username: str, password: str, role: str, email: str = None) -> "User":
        """
        创建新用户实例，自动处理密码哈希

        Args:
            username: 用户名
            password: 明文密码
            role: 用户角色
            email: 电子邮箱（可选）

        Returns:
            User: 用户实例
        """
        # 验证用户名格式
        if not cls.is_valid_username(username):
            raise ValueError("用户名格式不正确：3-50个字符，只允许字母、数字、下划线")

        # 验证密码长度
        if len(password) < 6:
            raise ValueError("密码长度至少为6个字符")

        # 验证角色
        if role not in ["admin", "teacher", "student"]:
            raise ValueError("角色必须是admin、teacher或student之一")

        # 生成密码哈希
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        return cls(
            username=username,
            password_hash=password_hash.decode('utf-8'),
            role=role,
            email=email,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @staticmethod
    def is_valid_username(username: str) -> bool:
        """
        验证用户名格式

        Args:
            username: 用户名

        Returns:
            bool: 用户名是否有效
        """
        if not username or len(username) < 3 or len(username) > 50:
            return False

        # 只允许字母、数字、下划线
        return username.replace("_", "").replace("-", "").isalnum()

    def verify_password(self, password: str) -> bool:
        """
        验证密码

        Args:
            password: 明文密码

        Returns:
            bool: 密码是否正确
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.password_hash.encode('utf-8')
            )
        except Exception:
            return False

    def set_password(self, password: str) -> None:
        """
        设置新密码

        Args:
            password: 新的明文密码
        """
        if len(password) < 6:
            raise ValueError("密码长度至少为6个字符")

        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式，用于API响应

        Returns:
            Dict[str, Any]: 用户信息字典（不包含密码哈希）
        """
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "email": self.email,
            "phone": self.phone,
            "student_id": self.student_id,
            "research_direction": self.research_direction,
            "status": self.status,
            "avatar": self.avatar,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        从字典创建用户实例

        Args:
            data: 包含用户信息的字典

        Returns:
            User: 用户实例
        """
        created_at = None
        updated_at = None

        if data.get("created_at"):
            if isinstance(data["created_at"], str):
                created_at = datetime.fromisoformat(data["created_at"])
            else:
                created_at = data["created_at"]

        if data.get("updated_at"):
            if isinstance(data["updated_at"], str):
                updated_at = datetime.fromisoformat(data["updated_at"])
            else:
                updated_at = data["updated_at"]

        return cls(
            id=data.get("id"),
            username=data.get("username", ""),
            password_hash=data.get("password_hash", ""),
            role=data.get("role", ""),
            email=data.get("email"),
            phone=data.get("phone"),
            student_id=data.get("student_id"),
            research_direction=data.get("research_direction"),
            status=data.get("status"),
            avatar=data.get("avatar"),
            created_at=created_at,
            updated_at=updated_at
        )

    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.role == "admin"

    def is_teacher(self) -> bool:
        """检查是否为老师"""
        return self.role == "teacher"

    def is_student(self) -> bool:
        """检查是否为学生"""
        return self.role == "student"