from app.database.models import LotteryPrizes, UserPrizes


async def get_available_nft_count(lottery_id: int) -> int:
    prize_ids = await LotteryPrizes.filter(lottery_id=lottery_id).values_list("prize_id", flat=True)
    used_count = await UserPrizes.filter(prize_id__in=prize_ids).count()
    total_count = len(prize_ids)
    
    return total_count - used_count