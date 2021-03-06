from gettext import gettext as _
from typing import Optional
from pydantic import validator, ValidationError, BaseModel
from fastapi_users import models
from fastapi_users.db import TortoiseBaseUserModel
from tortoise import fields, transactions, models as tmodels

from core.exceptions import x_username_exists_400
from core.utils import model_str

"""
DB
"""
class UserMod(TortoiseBaseUserModel):
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
    deleted_at =  fields.DatetimeField(null=True)
    updated_at =  fields.DatetimeField(auto_now=True)
    created_at =  fields.DatetimeField(auto_now_add=True)
    
    groups = fields.ManyToManyField('models.Group', related_name='group_users',
                                    through='auth_user_groups', backward_key='user_id')
    permissions = fields.ManyToManyField('models.Permission', related_name='permission_users',
                                         through='auth_user_permissions', backward_key='user_id')
    
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
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = 'auth_token'
    
    def __str__(self):
        return model_str(self, 'token')
    

"""
PYDANTIC
"""
class User(models.BaseUser):
    username: str
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