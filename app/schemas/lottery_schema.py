from pydantic import BaseModel, Field, ConfigDict


class ILotteryInfo(BaseModel):
    id: int
    title: str = Field(alias="name")
    shortDescription: str = Field(alias="short_description")
    banner: str
    headerBanner: str = Field(alias="collection_banner")
    eventDate: int = Field(alias="event_date")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class IFullLotteryInfo(ILotteryInfo):
    totalSum: int
    availableNftCount: int
    totalNftCount: int
    grandPrizes: list = []
    prizes: list = []
    winners: list = []
    otherLotteries: list[ILotteryInfo] = []
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class IGetLotteriesResponse(BaseModel):
    success: bool = True
    activeLottery: IFullLotteryInfo
    futureLotteries: list[ILotteryInfo]

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        ser_json_by_alias=True,
    )


class IPageRequest(BaseModel):
    page: int
    limit: int = 10
    q: str | None = None
    
    
class ILotteryHistoryInfo(BaseModel):
    id: int
    title: str = Field(alias="name")
    eventDate: int = Field(alias="event_date")
    totalNftCount: int
    nftCost: float = Field(alias="ticket_price")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    

class IGetLotteriesHistoryResponse(BaseModel):
    success: bool = True
    lotteries: list[ILotteryHistoryInfo]
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, ser_json_by_alias=True)
    
