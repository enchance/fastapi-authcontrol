from fastapi import Request
from fastapi_users.authentication import JWTAuthentication
from fastapi_users import FastAPIUsers
from fastapi_users.db import TortoiseUserDatabase

from app.settings import settings as s
from .models import User, UserCreate, UserUpdate, UserDB, UserMod
from app.AdminControl.models import Group
from .AuthControl import AuthControl


__version__ = "0.1"
__description__ = "AuthControl"
__author__ = "DropkickDev"


jwt_authentication = JWTAuthentication(secret=s.SECRET_KEY, lifetime_seconds=s.ACCESS_TOKEN_EXPIRE)

user_db = TortoiseUserDatabase(UserDB, UserMod)
fapi_user = FastAPIUsers(user_db, [jwt_authentication], User, UserCreate, UserUpdate, UserDB) # noqa

authcon = AuthControl()

async def signup_callback(user: UserDB, request: Request):
    # Add groups to the new user
    groups = await Group.filter(name__in=s.USER_GROUPS)
    user = await UserMod.get(pk=user.id).only('id')
    await user.groups.add(*groups)


async def user_callback(user: UserDB, updated_fields: dict, request: Request):
    pass
