from datetime import datetime

import aioredis
from fastapi import HTTPException
from sqlalchemy.orm import Session

from Posts.schemas import PostIn, PostUpdate
from Posts.models import Post, Like
from Accounts.models import User


def create_new_post(request: PostIn, user: User, db: Session):
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
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


def get_own_post(post_id: int, user: User, db: Session):
    """ Retrieves the post from the DB where requesting user is the author by post id """
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail=f"You can only update your own posts")
    return post


def get_post_to_like(post_id: int, user: User, db: Session):
    """ Retrieves the post that can be liked by the user (not their own) from the DB """
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id == user.id:
        raise HTTPException(status_code=403, detail="Cannot like/dislike own post")
    return post


def get_all_own_posts(user: User, db: Session):
    """ Retrieves all posts from the DB, where the requesting user is the post author """
    user_posts = db.query(Post).filter_by(author_id=user.id).all()
    if not user_posts:
        raise HTTPException(status_code=404, detail=f"You have no posts yet")
    return user_posts


def update_own_post(post_id: int, request: PostUpdate, user: User, db: Session):
    """ Updates the post in the DB, only if the requesting user is the post author """
    post = get_own_post(post_id, user, db)
    if request.title is not None:
        post.title = request.title
    if request.text is not None:
        post.text = request.text
    db.commit()
    db.refresh(post)
    return post


def delete_existing_post(post_id: int, user: User, db: Session):
    """ Deletes the post from the DB, only if the requesting user is the post author """
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")
    db.delete(post)
    db.commit()


def create_like(post: Post, dislike: bool, user: User, db: Session):
    """ Creates the Like object (like/dislike) in the DB for a post, by post id """
    like = db.query(Like).filter_by(user_id=user.id, post_id=post.id).first()
    if like:
        raise HTTPException(status_code=400, detail="Post already liked/disliked")
    new_like = Like(user_id=user.id, post_id=post.id, dislike=dislike)
    db.add(new_like)
    db.commit()
    db.refresh(post)
    return post


def get_like(post: Post, user: User, db: Session):
    """ Retrieves the Like object (like/dislike) from the DB if it exists """
    like = db.query(Like).filter_by(user_id=user.id, post_id=post.id).first()
    if not like:
        raise HTTPException(status_code=400, detail="Post not liked/disliked yet")
    return like


def delete_like(post: Post, user: User, db: Session):
    """ Deletes the Like object (like/dislike) from the DB if it exists """
    like = db.query(Like).filter_by(user_id=user.id, post_id=post.id).first()
    if not like:
        raise HTTPException(status_code=400, detail="Post not liked/disliked yet")
    db.delete(like)
    db.commit()
    db.refresh(post)
    return post


async def add_cache_like(redis, post_id: int, user_id: int, dislike: bool):
    """ Adds the user id to the set of users who liked/disliked the post """
    try:
        if dislike:
            await redis.sadd(f"{post_id}_dislikes", user_id)
        else:
            await redis.sadd(f"{post_id}_likes", user_id)
    except aioredis.RedisError as e:
        raise HTTPException(status_code=500, detail={"Redis error": str(e)})


async def get_cache_likes(redis, post_id: int):
    """ Retrieves post likes/dislikes user IDs sets by post id """
    try:
        likes = await redis.smembers(f"{post_id}_likes")
        dislikes = await redis.smembers(f"{post_id}_dislikes")
        return {"likes": [int(user_id) for user_id in likes],
                "dislikes": [int(user_id) for user_id in dislikes]}
    except aioredis.RedisError as e:
        raise HTTPException(status_code=500, detail={"Redis error": str(e)})


async def remove_cache_like(redis, post_id: int, user_id: int, dislike: bool):
    """ Removes the user id from the set of users who liked/disliked the post """
    try:
        if dislike:
            await redis.srem(f"{post_id}_dislikes", user_id)
        else:
            await redis.srem(f"{post_id}_likes", user_id)
    except aioredis.RedisError as e:
        raise HTTPException(status_code=500, detail={"Redis error": str(e)})


async def remove_cache_post(redis, post_id: int):
    """ Removes the sets of post likes/dislikes when post gets deleted """
    try:
        await redis.delete(f"{post_id}_dislikes", f"{post_id}_likes")
    except aioredis.RedisError as e:
        raise HTTPException(status_code=500, detail={"Redis error": str(e)})
