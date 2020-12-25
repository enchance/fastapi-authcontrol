from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Response, Depends, status, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from fastapi_users.router.common import ErrorCode
from tortoise.exceptions import DoesNotExist

from app.settings import settings as s
from . import fapi_user, signup_callback
from app.core.dependencies import unique_username, unique_email
from app.AdminControl.models import UniqueFieldsRegistration
from app.AuthControl import jwt_authentication, user_db, AuthControl
from app.AuthControl.models import UserMod, Token

router = APIRouter()
# router.include_router(fapi_user.get_auth_router(jwt_authentication))
router.include_router(fapi_user.get_register_router(signup_callback),
                      dependencies=[Depends(unique_username), Depends(unique_email)])
# router.include_router(fapi_user.get_users_router(user_callback))


@router.post('/token')
async def new_access_token(response: Response, refresh_token: Optional[str] = Cookie(None)):
    """
    Create a new access_token with the refresh_token cookie. If the refresh_token is still valid
    then a new access_token is generated. If it's expired then it is equivalent to being logged out.
    
    The refresh_token is renewed for every login to prevent accidental logouts.
    """
    cutoff_mins = 30
    try:
        if refresh_token is None:
            raise Exception

        # TODO: Access the cache instead of querying it
        token = await Token.get(token=refresh_token, is_blacklisted=False).only('expires',
                                                                                'author_id')
        user = await user_db.get(token.author_id)
        
        mins = AuthControl.expires(token.expires)
        if mins <= 0:
            raise Exception
        elif mins <= cutoff_mins:
            # refresh the refresh_token anyway before it expires
            try:
                token = await AuthControl.update_refresh_token(user)
            except DoesNotExist:
                token = await AuthControl.create_refresh_token(user)
            # token = {
            #     'value': 'FOOBAR',
            #     'expires': datetime(2020, 12, 30, 15)
            # }

            cookie = AuthControl.refresh_cookie(s.REFRESH_TOKEN_KEY, token)
            response.set_cookie(**cookie)

        data = await jwt_authentication.get_login_response(user, response)
        data.update({
            'mins': mins,
            'type': type(mins),
            'expires': token.expires,
            'now': datetime.utcnow(),
        })
        return data
    
    except (DoesNotExist, Exception) as e:
        del response.headers['authorization']
        response.delete_cookie(s.REFRESH_TOKEN_KEY)
        return dict(access_token='')


@router.post("/login")
async def login(response: Response, credentials: OAuth2PasswordRequestForm = Depends()):
    user = await fapi_user.db.authenticate(credentials)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )
    
    try:
        token = await AuthControl.update_refresh_token(user)
    except DoesNotExist:
        token = await AuthControl.create_refresh_token(user)

    cookie = AuthControl.refresh_cookie(s.REFRESH_TOKEN_KEY, token)
    response.set_cookie(**cookie)

    # TODO: Save user's permissions to cache
    # TODO: Save user's groups to cache
    # TODO: Save user data to cache

    return await jwt_authentication.get_login_response(user, response)


@router.get("/logout", dependencies=[Depends(fapi_user.get_current_active_user)])
async def logout(response: Response):
    """
    Logout the user by deleting all tokens. User can log out even if their access_token has already
    expired. Time will tell if this is right. Revert to commented code to only allow un-expired
    tokens to allow logouts.
    """
    # TODO: Delete user's permissions from the cache
    # TODO: Delete user's groups from the cache
    
    del response.headers['authorization']
    response.delete_cookie(s.REFRESH_TOKEN_KEY)
    return True


# @router.delete('/{id}', dependencies=[Depends(fapi_user.get_current_superuser)])
# async def delete_user(id: UUID4):
#     """
#     Soft-deletes the user instead of hard deleting them.
#     """
#     try:
#         user = await UserMod.get(id=id).only('id', 'deleted_at')
#         user.deleted_at = datetime.utcnow()
#         await user.save(update_fields=['deleted_at'])
#         return True
#     except DoesNotExist:
#         raise status.HTTP_404_NOT_FOUND


@router.post('/username')
async def check_username(inst: UniqueFieldsRegistration):
    exists = await UserMod.filter(username=inst.username).exists()
    return dict(exists=exists)


@router.post('/email')
async def check_username(inst: UniqueFieldsRegistration):
    exists = await UserMod.filter(email=inst.email).exists()
    return dict(exists=exists)


# @router.get('/readcookie')
# def readcookie(refresh_token: Optional[str] = Cookie(None)):
#     return refresh_token