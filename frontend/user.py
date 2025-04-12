from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class User(db.Model, UserMixin):
    __tablename__ = "user_details"
    u_key = db.Column(db.String(100), primary_key=True)
    uid = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    family_size = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.String(30), nullable=False)
    end_date = db.Column(db.String(30), nullable=False)
    active = db.Column(db.String(1), nullable=False)

    def get_id(self):
        return str(self.uid)


if __name__ == "__main__":
    User.create_user("admin", "1234")
