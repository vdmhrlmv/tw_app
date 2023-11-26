from datetime import datetime

from sqlalchemy import Column, ForeignKey, MetaData
from sqlalchemy import Text, Integer, DateTime, String
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = MetaData()


class Users(Base):
    __tablename__ = "users"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    email = Column(String(50), nullable=False, unique=True)
    apikey = Column(String(100), nullable=True, unique=True)
    last_activity = Column(DateTime, default=datetime.now)

    tweets = relationship("Tweets", back_populates="user", lazy="selectin")
    likes = relationship("Likes", back_populates="user", lazy="selectin")
    follower = relationship("Followers", back_populates="user", lazy="selectin")

    def __repr__(self):
        return f"User {self.id}: {self.name}, {self.email}, {self.apikey}"

    def to_json(self):
        json = {}
        for c in self.__table__.columns:
            if c.name == "last_activity":
                json[c.name] = str(getattr(self, c.name))
            else:
                json[c.name] = getattr(self, c.name)
        return json


class Tweets(Base):
    __tablename__ = "tweets"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    tweetdata = Column(Text)
    created_on = Column(DateTime, default=datetime.now)
    updated_on = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship(
        "Users", back_populates="tweets", cascade="all", lazy="selectin"
    )

    likes = relationship("Likes", back_populates="tweet", lazy="selectin")

    def __repr__(self):
        return f"Tweet {self.id}: {self.tweetdata}"

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Media(Base):
    __tablename__ = "media"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    filepath = Column(String(200), nullable=False)

    tweet_id = Column(Integer, nullable=True)

    def __repr__(self):
        return f"Media {self.id}: {self.tweet_id} {self.filepath}"

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Likes(Base):
    __tablename__ = "likes"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_on = Column(DateTime, default=datetime.now)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("Users", back_populates="likes", cascade="all", lazy="selectin")

    tweet_id = Column(Integer, ForeignKey("tweets.id"), nullable=False)
    tweet = relationship(
        "Tweets", back_populates="likes", cascade="all", lazy="selectin"
    )

    def __repr__(self):
        return f"Like {self.id}: user:{self.user_id} tweet:{self.tweet_id}"

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Followers(Base):
    __tablename__ = "followers"
    metadata = metadata
    id = Column(Integer, primary_key=True, autoincrement=True)
    follower_id = Column(Integer, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship(
        "Users", back_populates="follower", cascade="all", lazy="selectin"
    )

    def __repr__(self):
        return f"Follower:{self.follower_id}, user:{self.user_id}"

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
