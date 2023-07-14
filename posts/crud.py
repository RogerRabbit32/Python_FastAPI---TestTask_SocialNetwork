from datetime import datetime

from sqlalchemy.orm import Session

from posts.schemas import PostIn, PostUpdate
from posts.models import Post, Like
from accounts.models import User


def create_post(request: PostIn, user: User, db: Session):
    """ Creates new post in the DB, returning the Post model object """
    new_post = Post(
        title=request.title,
        text=request.text,
        author=user,
        created_at=datetime.utcnow()
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


def get_post_by_id(post_id: int, db: Session):
    """ Retrieves post from the DB by provided id """
    return db.query(Post).filter_by(id=post_id).first()


def get_own_post(post_id: int, user: User, db: Session):
    """ Retrieves post from the DB, where the
        requesting user is the post author, by post id """
    return db.query(Post).filter_by(id=post_id, author_id=user.id).first()


def get_all_own_posts(user: User, db: Session):
    """ Retrieves all posts from the DB, where
        the requesting user is the post author """
    return db.query(Post).filter_by(author_id=user.id).all()


def update_post(post_id: int, request: PostUpdate, db: Session):
    """ Updates post in the DB, should be available
        only if the requesting user is the post author """
    post = db.query(Post).filter_by(id=post_id).first()
    if request.title is not None:
        post.title = request.title
    if request.text is not None:
        post.text = request.text
    db.commit()
    db.refresh(post)
    return post


def delete_existing_post(post_id: int, db: Session):
    """ Deletes post from the DB, should be available
        only if the requesting user is the post author """
    post = db.query(Post).filter_by(id=post_id).first()
    db.delete(post)
    db.commit()


def get_like(post_id: int, user: User, db: Session):
    """ Retrieves Like object (like/dislike) from the DB """
    return db.query(Like).filter_by(user_id=user.id, post_id=post_id).first()


def create_like(post_id: int, dislike: bool, user: User, db: Session):
    """ Creates a Like object (like/dislike) in the DB for a post, by post id """
    new_like = Like(user_id=user.id, post_id=post_id, dislike=dislike)
    db.add(new_like)
    db.commit()
    return new_like


def delete_like(post_id: int, user: User, db: Session):
    """ Deletes Like object (like/dislike) from the DB if it exists """
    like = db.query(Like).filter_by(user_id=user.id, post_id=post_id).first()
    db.delete(like)
    db.commit()


async def add_cache_like(redis, post_id: int, user_id: int, dislike: bool):
    """ Adds the provided user id to the set of users who liked/disliked the post """
    if dislike:
        await redis.sadd(f"{post_id}_dislikes", user_id)
    else:
        await redis.sadd(f"{post_id}_likes", user_id)


async def get_cache_likes(redis, post_id: int):
    """ Retrieves post likes/dislikes user IDs sets by post id """
    likes = await redis.smembers(f"{post_id}_likes")
    dislikes = await redis.smembers(f"{post_id}_dislikes")
    return {"likes": [int(user_id) for user_id in likes],
            "dislikes": [int(user_id) for user_id in dislikes]}


async def check_cache_like(redis, post_id: int, user_id: int):
    """ Checks if the user's like already exists in the Redis cache """
    redis_likes = await redis.smembers(f"{post_id}_likes")
    redis_dislikes = await redis.smembers(f"{post_id}_dislikes")
    likes = [int(user_id) for user_id in redis_likes]
    dislikes = [int(user_id) for user_id in redis_dislikes]
    return user_id in likes or user_id in dislikes


async def remove_cache_like(redis, post_id: int, user_id: int, dislike: bool):
    """ Removes the user id from the set of users who liked/disliked the post """
    if dislike:
        await redis.srem(f"{post_id}_dislikes", user_id)
    else:
        await redis.srem(f"{post_id}_likes", user_id)


async def remove_cache_post(redis, post_id: int):
    """ Removes the sets of post likes/dislikes from cache when post gets deleted """
    await redis.delete(f"{post_id}_dislikes", f"{post_id}_likes")
