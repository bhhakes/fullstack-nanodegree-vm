# SQLAlchemy Import Configurations
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

# Other Import Configurations
from passlib.apps import custom_app_context as pwd_context
import random
import string
from itsdangerous \
    import(TimedJSONWebSignatureSerializer
           as Serializer, BadSignature, SignatureExpired)

Base = declarative_base()

# This secret key creates and verifies your tokens
secret_key = ''.join(random.choice(string.ascii_uppercase + string.digits)
                     for x in xrange(32))


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
                'name': self.name,
                'email': self.name,
                'picture': self.name,
        }


class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
                'name': self.name,
        }


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    category_name = Column(String, ForeignKey("category.name"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
                'name': self.title,
                'description': self.description,
                'category_name': self.category_name,
        }


# create instance of sqlite for our catalog db
engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
