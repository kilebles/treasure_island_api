from tortoise import fields
from tortoise.models import Model


class Prize(Model):
    id = fields.BigIntField(pk=True)
    title = fields.CharField(max_length=255)
    type = fields.CharField(max_length=255)
    description = fields.TextField()
    quantity = fields.IntField()
    winners = fields.BigIntField(null=True)
    image = fields.CharField(max_length=255)

    user_prizes: fields.ReverseRelation["UserPrizes"]
    lottery_prizes: fields.ReverseRelation["LotteryPrizes"]