from tortoise import fields
from tortoise.models import Model


class UserPrizes(Model):
    id = fields.BigIntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="prizes")
    prize = fields.ForeignKeyField("models.Prize", related_name="user_prizes")