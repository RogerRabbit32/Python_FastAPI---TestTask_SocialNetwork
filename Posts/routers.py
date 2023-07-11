from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from Accounts.models import User
from Accounts.authorization import get_current_user
from Posts.schemas import PostIn, PostOut, PostUpdate
from Posts.models import Post, Like

router = APIRouter(tags=["Posts"])


@router.get('/', response_model=List[PostOut])
def get_all_posts(limit: int = Query(10, gt=0), offset: int = Query(0, ge=0),
                  db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    posts = db.query(Post).offset(offset).limit(limit).all()
    return posts


@router.get('/user', response_model=List[PostOut])
def get_user_posts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_posts = db.query(Post).filter_by(author_id=current_user.id).all()
    if not user_posts:
        raise HTTPException(status_code=404, detail=f"You have no posts yet")
    return user_posts


@router.get('/{post_id}', response_model=PostOut)
def get_single_post(post_id: int, db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.post('/', status_code=201, response_model=PostOut)
def create_post(request: PostIn, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    try:
        new_post = Post(
            title=request.title,
            text=request.text,
            author=current_user,
            created_at=datetime.utcnow()
        )
        db.add(new_post)
        db.commit()
        db.refresh(new_post)
        return new_post
    except Exception as e:
        return {"detail": e}


@router.delete('/{post_id}', status_code=204)
def delete_post(post_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail=f"You can only delete your own posts")
    db.delete(post)
    db.commit()


@router.put('/{post_id}', response_model=PostOut)
def update_post(post_id: int, request: PostUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail=f"You can only update your own posts")

    if request.title is not None:
        post.title = request.title
    if request.text is not None:
        post.text = request.text

    db.commit()
    db.refresh(post)
    return post


@router.post('/{post_id}/like', response_model=PostOut)
def like_post(post_id: int, dislike: bool = False, db: Session = Depends(get_db),
              current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot like/dislike own post")
    like = db.query(Like).filter_by(user_id=current_user.id, post_id=post_id).first()
    if like:
        raise HTTPException(status_code=400, detail="Post already liked/disliked")
    new_like = Like(user_id=current_user.id, post_id=post_id, dislike=dislike)
    db.add(new_like)
    db.commit()
    db.refresh(post)
    return post


@router.delete('/{post_id}/like', response_model=PostOut)
def unlike_post(post_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id == current_user.id:
        raise HTTPException(status_code=403, detail="Cannot unlike own post")
    like = db.query(Like).filter_by(user_id=current_user.id, post_id=post_id).first()
    if not like:
        raise HTTPException(status_code=400, detail="Post not liked/disliked yet")
    db.delete(like)
    db.commit()
    db.refresh(post)
    return post


@router.get('/{post_id}/likes')
def get_post_likes(post_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter_by(id=post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post_likes = db.query(Like).filter_by(post_id=post_id).all()
    if post_likes:
        return post_likes
    else:
        return {"detail": "Post has no likes or dislikes yet"}
