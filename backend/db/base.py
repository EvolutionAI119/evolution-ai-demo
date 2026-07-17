"""SQLAlchemy Declarative Base。"""
from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""

    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        # 类名转 snake_case 表名
        name = cls.__name__
        snake = []
        for i, ch in enumerate(name):
            if ch.isupper() and i > 0 and not name[i - 1].isupper():
                snake.append("_")
            snake.append(ch.lower())
        return "".join(snake)
