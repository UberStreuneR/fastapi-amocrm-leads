from sqlalchemy.orm import declared_attr
from sqlmodel import Session, SQLModel
from sqlmodel import create_engine
from .settings_ import settings

engine = create_engine(url=settings.database)


def get_session() -> Session:
    """Получить сессию, при возвращении в функцию - закомитить ее"""

    with Session(engine) as session:
        yield session
        session.commit()
        print("Session committed")


class DatabaseModel(SQLModel):
    """Базовый класс для моделей бд"""

    @declared_attr
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

    @classmethod
    def create(cls, session: Session, **fields) -> "DatabaseModel":
        """Создать инстанс класса"""

        instance = cls(**fields)
        session.add(instance)
        session.flush([instance])

        return instance

    def update(self, session: Session, **fields):
        """Обновить инстанс класса"""

        # Валидируем итоговую модель
        model = self.__class__(**{**self.dict(), **fields})

        for field, value in model.dict().items():
            setattr(self, field, value)

        session.add(self)
        session.flush([self])
