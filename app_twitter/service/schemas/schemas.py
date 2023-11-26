from pydantic import BaseModel, Field
from pydantic.class_validators import Optional


class BaseTweet(BaseModel):
    tweet_data: str
    tweet_media_ids: tuple
