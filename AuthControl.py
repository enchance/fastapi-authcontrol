import secrets
from datetime import timedelta
from datetime import datetime
from enum import Enum
from . import UserDB
from .models import UserMod, Token
from app.settings import settings as s


class TimeUnits(Enum):
    days = 'days'
    hours = 'hours'
    minutes = 'minutes'
    seconds = 'seconds'


class TokenCode(Enum):
    refresh = 'refresh'
    access = 'access'


class AuthControl:
    
    @staticmethod
    def generate_refresh_token(nbytes: int = 32):
        return secrets.token_hex(nbytes=nbytes)

    @staticmethod
    def time_difference(*, start: datetime, end: datetime):
        """Get the diff between 2 dates"""
        diff = end - start
    
        return {
            'days': diff.days,
            'hours': int(diff.total_seconds()) // 3600,
            'minutes': int(diff.total_seconds()) // 60,
            'seconds': int(diff.total_seconds()),
        }
    
    @classmethod
    def refresh_cookie(cls, name: str, token: dict, **kwargs):
        if token['expires'] <= datetime.utcnow():
            raise ValueError('Cookie expires date must be greater than the date now')
        
        expires = token['expires'] - datetime.utcnow()
        cookie_data = {
            'key': name,
            'value': token['value'],
            'httponly': True,
            'expires': expires.seconds,
            'path': '/',
            **kwargs,
        }
        # if not s.DEBUG:
        #     cookie_data.update({
        #         'secure': True
        #     })
        return cookie_data
        
    @classmethod
    def expires(cls, expires: datetime, units: str = 'minutes'):
        now = datetime.utcnow()
        diff = cls.time_difference(start=now, end=expires)
        return diff[units]


    @classmethod
    async def create_refresh_token(cls, user: UserDB) -> dict:
        """
        Create and save a new refresh token
        :param user Pydantic model for the user
        """
        refresh_token = AuthControl.generate_refresh_token()
        expires = datetime.utcnow() + timedelta(seconds=s.REFRESH_TOKEN_EXPIRE)
    
        user = await UserMod.get(pk=user.id).only('id')
        await Token.create(token=refresh_token, expires=expires, author=user)
        return {
            'value': refresh_token,
            'expires': expires,
        }
    
    
    @classmethod
    async def update_refresh_token(cls, user: UserDB) -> dict:
        """
        Update the refresh token of the user
        :param user Pydantic model for the user
        """
        refresh_token = AuthControl.generate_refresh_token()
        expires = datetime.utcnow() + timedelta(seconds=s.REFRESH_TOKEN_EXPIRE)
    
        token = await Token.get(author_id=user.id, is_blacklisted=False).only('id', 'token',
                                                                              'expires')
        token.token = refresh_token
        token.expires = expires
        await token.save(update_fields=['token', 'expires'])
        return {
            'value': refresh_token,
            'expires': expires,
        }

