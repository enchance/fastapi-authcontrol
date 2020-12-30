from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel
from fastapi_users import models
from fastapi_users.db import TortoiseBaseUserModel, tortoise
from tortoise import fields, models as tmodels

from app.core.utils import model_str
from app.core.models import DTMixin



"""
DB
"""
class UserMod(DTMixin, TortoiseBaseUserModel):
    username =    fields.CharField(max_length=50, null=True)
    first_name =  fields.CharField(max_length=191, default='')
    middle_name = fields.CharField(max_length=191, default='')
    last_name =   fields.CharField(max_length=191, default='')

    civil =     fields.CharField(max_length=20, default='')
    bday =      fields.DateField(null=True)
    mobile =    fields.CharField(max_length=50, default='')
    telephone = fields.CharField(max_length=50, default='')
    avatar =    fields.CharField(max_length=191, default='')
    status =    fields.CharField(max_length=20, default='')
    bio =       fields.CharField(max_length=191, default='')
    address1 =  fields.CharField(max_length=191, default='')
    address2 =  fields.CharField(max_length=191, default='')
    country =   fields.CharField(max_length=2, default='')
    zipcode =   fields.CharField(max_length=20, default='')
    timezone =  fields.CharField(max_length=10, default='+00:00')
    website =   fields.CharField(max_length=191, default='')
    
    is_verified = fields.BooleanField(default=False)
    last_login =  fields.DatetimeField(null=True)
    
    groups = fields.ManyToManyField('models.Group', related_name='group_users',
                                    through='auth_user_groups', backward_key='user_id')
    permissions = fields.ManyToManyField('models.Permission', related_name='permission_users',
                                         through='auth_user_permissions', backward_key='user_id')
    
    starter_fields = [*tortoise.starter_fields, 'username', 'timezone', 'is_verified']
    
    class Meta:
        table = 'auth_user'

    @property
    def fullname(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    async def display_name(self):
        if self.username:
            return self.username
        elif self.fullname:
            return self.fullname.split()[0]
        else:
            return self.email.split('@')[0]
    
    async def to_dict(self):
        d = {}
        for field in self.starter_fields:
            d[field] = getattr(self, field)
        return d
    
    # TODO: has_perm        
    async def has_perm(self, perm_code: str):
        pass
    
    
    # TODO: has_group
    async def has_group(self, group_name: str):
        pass


class Token(tmodels.Model):
    token = fields.CharField(max_length=128, index=True)
    expires = fields.DatetimeField(index=True)
    # is_expired = fields.BooleanField(default=False)
    is_blacklisted = fields.BooleanField(default=False)
    author = fields.ForeignKeyField('models.UserMod', on_delete=fields.CASCADE,
                                    related_name='tokens_author')
    # created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = 'auth_token'
    
    def __str__(self):
        return model_str(self, 'token')
    

"""
PYDANTIC
"""
class User(models.BaseUser):
    username: str
    timezone: str
    is_verified: bool
    # pass


class UserCreate(models.BaseUserCreate):
    username: str

    # @validator('email')
    # def nonum(cls, email):
    #     if '5' in email:
    #         raise ValueError('No number 5 allowed.')
    #     return email


class UserUpdate(User, models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB):
    pass


class TokenCreate(BaseModel):
    id: int
    token: str


class OptionCreate(BaseModel):
    name: str
    value: str
    user: Optional[UserDB]


class OptionUpdate(BaseModel):
    id: int
    value: str
    user: Optional[UserDB]


class OptionDelete(BaseModel):
    id: int
    user: Optional[UserDB]
