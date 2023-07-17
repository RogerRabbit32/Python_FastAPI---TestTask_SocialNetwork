from typing import List

import aioredis
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from accounts.models import User
from accounts.authorization import get_current_user
from posts.schemas import PostIn, PostOut, PostUpdate
from posts.crud import create_post, get_posts, get_post_by_id, get_own_post, get_all_own_posts, \
    update_post, delete_existing_post, create_like, get_like, delete_like, add_cache_like, \
    remove_cache_like, remove_cache_post, get_cache_likes, check_cache_like, update_cache


router = APIRouter(tags=["Posts"])

REDIS = aioredis.from_url("redis://redis")


@router.post('/', status_code=201, response_model=PostOut)
def create_new_post(request: PostIn, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    return create_post(request, current_user, db)


@router.get('/', response_model=List[PostOut])
def get_all_posts(limit: int = Query(10, gt=0), offset: int = Query(0, ge=0),
                  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_posts(limit, offset, db)


@router.get('/user', response_model=List[PostOut])
def get_user_posts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_posts = get_all_own_posts(current_user, db)
    if not user_posts:
        raise HTTPException(status_code=404, detail=f"You have no posts yet")
    return user_posts


@router.get('/{post_id}', response_model=PostOut)
def get_single_post(post_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    post = get_post_by_id(post_id, db)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put('/{post_id}', response_model=PostOut)
def update_user_post(post_id: int, request: PostUpdate, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    user_post = get_own_post(post_id, current_user, db)
    if user_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return update_post(post_id, request, db)


@router.delete('/{post_id}', status_code=204)
async def delete_post(post_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    user_post = get_own_post(post_id, current_user, db)
    if user_post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    # Redis cache functionality: delete the post likes and dislikes
    await remove_cache_post(REDIS, post_id)

    # Delete post from the DB (with its likes/dislikes)
    delete_existing_post(post_id, db)


@router.post('/{post_id}/like', response_model=PostOut)
async def like_post(post_id: int, dislike: bool = False, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    # Check if the user's like doesn't already exist in the Redis cache
    existing_like = await check_cache_like(REDIS, post_id, current_user.id)
    if existing_like:
        raise HTTPException(status_code=403, detail="Post already liked/disliked")

    # Check if post exists and doesn't belong to the requesting user
    existing_post = get_post_by_id(post_id, db)
    if existing_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing_post.author_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot like/dislike own post")

    # Redis cache functionality: save like/dislike as a post_id/user_id pair
    await add_cache_like(REDIS, post_id, current_user.id, dislike)

    # Create like/dislike object in the DB
    create_like(post_id, dislike, current_user, db)
    return existing_post


@router.delete('/{post_id}/like', response_model=PostOut)
async def unlike_post(post_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    # Check if the user's like already exists in the Redis cache
    existing_like = await check_cache_like(REDIS, post_id, current_user.id)
    if not existing_like:
        raise HTTPException(status_code=400, detail="Post not liked/disliked yet")

    # Check if post exists and doesn't belong to the requesting user
    existing_post = get_post_by_id(post_id, db)
    if existing_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if existing_post.author_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot like/dislike own post")

    like = get_like(post_id, current_user, db)
    # Redis cache functionality: delete like from cache
    await remove_cache_like(REDIS, post_id, current_user.id, like.dislike)

    # Delete like from DB
    delete_like(post_id, current_user, db)
    return existing_post


@router.get('/{post_id}/likes')
async def get_post_likes(post_id: int, db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    # If cache is empty (due to lifetime expiration or some error),
    # it needs to get refilled from the DB
    if await check_cache_like(REDIS, post_id, -1) is False:
        await update_cache(REDIS, post_id, db)
    return await get_cache_likes(REDIS, post_id)
