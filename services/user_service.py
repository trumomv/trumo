from sqlalchemy.orm import Session
from models import User
from pydantic_models.user import UserCreate


class UserService:

    @classmethod
    def fetch(cls, db: Session, user_id: int) -> User:
        return db.query(User).get(user_id)

    @classmethod
    def create_user(cls, db: Session, user: UserCreate) -> User:
        db_user = User()
        db_user.name = user.name
        db_user.balance = user.balance
        db.add(db_user)

        return db_user

    @classmethod
    def get_users(cls, db: Session):
        return db.query(User).order_by(User.name).all()
