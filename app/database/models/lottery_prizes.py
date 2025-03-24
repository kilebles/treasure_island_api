from tortoise import fields
from tortoise.models import Model


class LotteryPrizes(Model):
    id = fields.BigIntField(pk=True)
    lottery = fields.ForeignKeyField("models.Lottery", related_name="lottery_prizes")
    prize = fields.ForeignKeyField("models.Prize", related_name="lottery_prizes")