from typing import List

import aioredis
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from Accounts.models import User
from Accounts.authorization import get_current_user
from Posts.schemas import PostIn, PostOut, PostUpdate
from Posts.models import Post
from Posts.crud import create_new_post, get_post_by_id, get_all_own_posts, \
    update_own_post, delete_existing_post, get_post_to_like, create_like, \
    get_like, delete_like, add_cache_like, remove_cache_like, remove_cache_post, \
    get_cache_likes


router = APIRouter(tags=["Posts"])


@router.get('/', response_model=List[PostOut])
def get_all_posts(limit: int = Query(10, gt=0), offset: int = Query(0, ge=0),
                  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    posts = db.query(Post).offset(offset).limit(limit).all()
    return posts


@router.get('/user', response_model=List[PostOut])
def get_user_posts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_all_own_posts(current_user, db)


@router.get('/{post_id}', response_model=PostOut)
def get_single_post(post_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    return get_post_by_id(post_id, db)


@router.post('/', status_code=201, response_model=PostOut)
def create_post(request: PostIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    return create_new_post(request, current_user, db)


@router.delete('/{post_id}', status_code=204)
async def delete_post(post_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    delete_existing_post(post_id, current_user, db)

    # Redis cache functionality: delete the post likes and dislikes
    redis = aioredis.from_url("redis://localhost")
    await remove_cache_post(redis, post_id)


@router.put('/{post_id}', response_model=PostOut)
def update_post(post_id: int, request: PostUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    return update_own_post(post_id, request, current_user, db)


@router.post('/{post_id}/like', response_model=PostOut)
async def like_post(post_id: int, dislike: bool = False, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    post_to_like = get_post_to_like(post_id, current_user, db)
    liked_post = create_like(post_to_like, dislike, current_user, db)

    # Redis cache functionality: save the like as a post_id/user_id pair
    redis = aioredis.from_url("redis://localhost")
    await add_cache_like(redis, post_id, current_user.id, dislike)

    return liked_post


@router.delete('/{post_id}/like', response_model=PostOut)
async def unlike_post(post_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    post_to_unlike = get_post_to_like(post_id, current_user, db)
    like = get_like(post_to_unlike, current_user, db)

    # Redis cache functionality: delete the like from cache
    redis = aioredis.from_url("redis://localhost")
    await remove_cache_like(redis, post_id, current_user.id, like.dislike)

    return delete_like(post_to_unlike, current_user, db)


@router.get('/{post_id}/likes')
async def get_post_likes(post_id: int, current_user: User = Depends(get_current_user)):
    redis = aioredis.from_url("redis://localhost")
    return await get_cache_likes(redis, post_id)
