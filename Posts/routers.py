from fastapi import APIRouter, Depends, HTTPException

from schemas import PostIn, PostOut

router = APIRouter(tags=["Posts"])


@router.get('/')
def get_all_posts(limit=10):
    return {'data': f'{limit} posts_list'}


@router.get('/{post_id}', response_model=PostOut)
def get_single_post(post_id: int):
    return {'data': post_id}


@router.post('/', response_model=PostOut)
def create_post(request: PostIn):
    pass

