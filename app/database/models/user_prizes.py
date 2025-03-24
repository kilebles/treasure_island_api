from tortoise import fields
from tortoise.models import Model


class UserPrizes(Model):
    id = fields.BigIntField(pk=True)
    user = fields.ForeignKeyField("app.User", related_name="prizes")
    prize = fields.ForeignKeyField("app.Prize", related_name="user_prizes")
    
    class Meta:
        app = "app"