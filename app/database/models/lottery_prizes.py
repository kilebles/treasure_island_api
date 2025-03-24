from tortoise import fields
from tortoise.models import Model


class LotteryPrizes(Model):
    id = fields.BigIntField(pk=True)
    lottery = fields.ForeignKeyField("app.Lottery", related_name="lottery_prizes")
    prize = fields.ForeignKeyField("app.Prize", related_name="lottery_prizes")
    
    class Meta:
        app = "app"