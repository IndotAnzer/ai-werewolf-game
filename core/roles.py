from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RoleType(Enum):
    WEREWOLF = "werewolf"
    VILLAGER = "villager"
    PROPHET = "prophet"
    WITCH = "witch"
    HUNTER = "hunter"
    IDIOT = "idiot"
    GUARDIAN = "guardian"
    CUPID = "cupid"
    ELDER = "elder"
    BEAR_TAMER = "bear_tamer"
    GRAVEYARD_KEEPER = "graveyard_keeper"
    WHITE_WEREWOLF_KING = "white_werewolf_king"
    WOLF_BEAUTY = "wolf_beauty"
    WOLF_PROPHET = "wolf_prophet"
    INFECTED_WEREWOLF = "infected_werewolf"


class Camp(Enum):
    VILLAGER = "villager"
    WEREWOLF = "werewolf"
    THIRD_PARTY = "third_party"


class Role(BaseModel):
    role_type: RoleType
    name: str
    camp: Camp
    description: str
    abilities: List[str] = Field(default_factory=list)


ROLES = {
    RoleType.VILLAGER: Role(
        role_type=RoleType.VILLAGER,
        name="村民",
        camp=Camp.VILLAGER,
        description="普通村民，没有特殊技能",
        abilities=["投票"]
    ),
    RoleType.PROPHET: Role(
        role_type=RoleType.PROPHET,
        name="预言家",
        camp=Camp.VILLAGER,
        description="每晚可以查验一名玩家的身份",
        abilities=["查验身份"]
    ),
    RoleType.WITCH: Role(
        role_type=RoleType.WITCH,
        name="女巫",
        camp=Camp.VILLAGER,
        description="拥有一瓶解药和一瓶毒药",
        abilities=["使用解药", "使用毒药"]
    ),
    RoleType.HUNTER: Role(
        role_type=RoleType.HUNTER,
        name="猎人",
        camp=Camp.VILLAGER,
        description="死亡时可以带走一名玩家",
        abilities=["开枪带走"]
    ),
    RoleType.IDIOT: Role(
        role_type=RoleType.IDIOT,
        name="白痴",
        camp=Camp.VILLAGER,
        description="被投票出局时不会死亡",
        abilities=["翻牌存活"]
    ),
    RoleType.GUARDIAN: Role(
        role_type=RoleType.GUARDIAN,
        name="守卫",
        camp=Camp.VILLAGER,
        description="每晚可以守护一名玩家",
        abilities=["守护"]
    ),
    RoleType.CUPID: Role(
        role_type=RoleType.CUPID,
        name="丘比特",
        camp=Camp.VILLAGER,
        description="第一晚可以选择两名玩家成为情侣",
        abilities=["指定情侣"]
    ),
    RoleType.ELDER: Role(
        role_type=RoleType.ELDER,
        name="长老",
        camp=Camp.VILLAGER,
        description="拥有两条生命",
        abilities=["两条生命"]
    ),
    RoleType.BEAR_TAMER: Role(
        role_type=RoleType.BEAR_TAMER,
        name="驯熊人",
        camp=Camp.VILLAGER,
        description="熊咆哮意味着场上有狼人存活",
        abilities=["熊咆哮"]
    ),
    RoleType.GRAVEYARD_KEEPER: Role(
        role_type=RoleType.GRAVEYARD_KEEPER,
        name="守墓人",
        camp=Camp.VILLAGER,
        description="每晚可以得知当天白天被投票出局的玩家阵营",
        abilities=["查验死者阵营"]
    ),
    RoleType.WEREWOLF: Role(
        role_type=RoleType.WEREWOLF,
        name="狼人",
        camp=Camp.WEREWOLF,
        description="每晚可以杀死一名玩家",
        abilities=["杀人"]
    ),
    RoleType.WHITE_WEREWOLF_KING: Role(
        role_type=RoleType.WHITE_WEREWOLF_KING,
        name="白狼王",
        camp=Camp.WEREWOLF,
        description="自爆时可以带走一名玩家",
        abilities=["自爆带人"]
    ),
    RoleType.WOLF_BEAUTY: Role(
        role_type=RoleType.WOLF_BEAUTY,
        name="狼美人",
        camp=Camp.WEREWOLF,
        description="每晚可以魅惑一名玩家",
        abilities=["魅惑"]
    ),
    RoleType.WOLF_PROPHET: Role(
        role_type=RoleType.WOLF_PROPHET,
        name="狼先知",
        camp=Camp.WEREWOLF,
        description="可以伪装成预言家",
        abilities=["伪装预言家"]
    ),
    RoleType.INFECTED_WEREWOLF: Role(
        role_type=RoleType.INFECTED_WEREWOLF,
        name="种狼",
        camp=Camp.WEREWOLF,
        description="感染一名玩家",
        abilities=["感染"]
    ),
}


def get_role(role_type: RoleType) -> Role:
    return ROLES[role_type]


def get_recommended_roles(player_count: int) -> List[RoleType]:
    if player_count == 6:
        return [RoleType.WEREWOLF, RoleType.WEREWOLF,
                RoleType.PROPHET, RoleType.WITCH, RoleType.HUNTER, RoleType.VILLAGER]
    elif player_count == 9:
        return [RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.WEREWOLF,
                RoleType.PROPHET, RoleType.WITCH, RoleType.HUNTER,
                RoleType.VILLAGER, RoleType.VILLAGER, RoleType.VILLAGER]
    elif player_count == 12:
        return [RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.WEREWOLF, RoleType.WEREWOLF,
                RoleType.PROPHET, RoleType.WITCH, RoleType.HUNTER, RoleType.IDIOT,
                RoleType.VILLAGER, RoleType.VILLAGER, RoleType.VILLAGER, RoleType.VILLAGER]
    else:
        werewolf_count = max(2, player_count // 3)
        villager_count = player_count - werewolf_count
        roles = [RoleType.WEREWOLF] * werewolf_count
        roles.extend([RoleType.VILLAGER] * villager_count)
        return roles
