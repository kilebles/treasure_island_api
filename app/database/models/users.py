from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.BigIntField(pk=True)
    telegram = fields.BigIntField(unique=True)
    first_name = fields.CharField(max_length=255, null=True)
    last_name = fields.CharField(max_length=255, null=True)
    username = fields.CharField(max_length=255, null=True)
    photo = fields.CharField(max_length=255, null=True)
    registered_at = fields.DatetimeField(auto_now_add=True)
    
    profile: fields.ReverseRelation["UserProfile"]
    tickets: fields.ReverseRelation["Ticket"]
    prizes: fields.ReverseRelation["UserPrizes"]
    
    class Meta:
        app = "app"