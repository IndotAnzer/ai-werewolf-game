from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
from core.roles import RoleType, Camp, Role, get_role


class GamePhase(Enum):
    SETUP = "setup"
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"
    GAME_OVER = "game_over"


class PlayerStatus(Enum):
    ALIVE = "alive"
    DEAD = "dead"
    IDIOT_REVEALED = "idiot_revealed"


class Player(BaseModel):
    player_id: int
    name: str
    role_type: RoleType
    is_agent: bool = True
    personality: str = ""
    personality_prompt: str = ""
    status: PlayerStatus = PlayerStatus.ALIVE
    votes: int = 0
    is_sheriff: bool = False
    lovers: List[int] = Field(default_factory=list)
    charmed_by: Optional[int] = None
    has_been_infected: bool = False
    elder_lives: int = 2
    witch_has_potion: bool = True
    witch_has_poison: bool = True
    last_guarded: Optional[int] = None
    memories: List[str] = Field(default_factory=list)
    private_info: Dict = Field(default_factory=dict)
    
    @property
    def role(self) -> Role:
        return get_role(self.role_type)
    
    @property
    def camp(self) -> Camp:
        if self.has_been_infected:
            return Camp.WEREWOLF
        return self.role.camp


class GameLog(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    phase: GamePhase
    message: str
    public: bool = True
    visible_to: List[int] = Field(default_factory=list)


class GameState(BaseModel):
    game_id: str
    phase: GamePhase = GamePhase.SETUP
    day_count: int = 0
    night_count: int = 0
    players: Dict[int, Player] = Field(default_factory=dict)
    logs: List[GameLog] = Field(default_factory=list)
    dead_players: List[int] = Field(default_factory=list)
    werewolf_vote: Optional[int] = None
    prophet_check: Optional[Tuple[int, bool]] = None
    witch_action: Optional[Tuple[str, int]] = None
    guardian_protect: Optional[int] = None
    cupid_lovers: Optional[Tuple[int, int]] = None
    night_kill_target: Optional[int] = None
    last_words: Dict[int, str] = Field(default_factory=dict)
    current_speaker: Optional[int] = None
    speaking_order: List[int] = Field(default_factory=list)
    sheriff_candidate: List[int] = Field(default_factory=list)
    sheriff_elected: bool = False
    wolf_beauty_charmed: Optional[int] = None
    game_winner: Optional[Camp] = None
    
    def add_player(self, player: Player) -> None:
        self.players[player.player_id] = player
    
    def get_alive_players(self) -> List[Player]:
        return [p for p in self.players.values() if p.status == PlayerStatus.ALIVE or p.status == PlayerStatus.IDIOT_REVEALED]
    
    def get_alive_player_ids(self) -> List[int]:
        return [p.player_id for p in self.get_alive_players()]
    
    def get_werewolves(self) -> List[Player]:
        return [p for p in self.players.values() if p.camp == Camp.WEREWOLF and p.status == PlayerStatus.ALIVE]
    
    def get_villagers(self) -> List[Player]:
        return [p for p in self.players.values() if p.camp == Camp.VILLAGER and (p.status == PlayerStatus.ALIVE or p.status == PlayerStatus.IDIOT_REVEALED)]
    
    def add_log(self, message: str, public: bool = True, visible_to: Optional[List[int]] = None) -> None:
        log = GameLog(
            phase=self.phase,
            message=message,
            public=public,
            visible_to=visible_to or []
        )
        self.logs.append(log)
    
    def get_player(self, player_id: int) -> Optional[Player]:
        return self.players.get(player_id)
    
    def kill_player(self, player_id: int, reason: str = "") -> None:
        player = self.get_player(player_id)
        if not player or player.status != PlayerStatus.ALIVE:
            return
        
        if player.role_type == RoleType.ELDER and player.elder_lives > 1:
            player.elder_lives -= 1
            self.add_log(f"{player.name} 长老失去了一条生命", public=False)
            return
        
        if player.role_type == RoleType.IDIOT and self.phase == GamePhase.VOTING:
            player.status = PlayerStatus.IDIOT_REVEALED
            self.add_log(f"{player.name} 被投票出局，但翻开身份牌继续存活", public=True)
            return
        
        player.status = PlayerStatus.DEAD
        self.dead_players.append(player_id)
        self.add_log(f"{player.name} 死亡了！{reason}", public=True)
        
        for lover_id in player.lovers:
            lover = self.get_player(lover_id)
            if lover and lover.status == PlayerStatus.ALIVE:
                self.kill_player(lover_id, f"因为情侣 {player.name} 死亡而殉情")
        
        if player.role_type == RoleType.WOLF_BEAUTY and player.charmed_by == player_id:
            charmed = self.get_player(self.wolf_beauty_charmed)
            if charmed and charmed.status == PlayerStatus.ALIVE:
                self.kill_player(charmed.player_id, f"因为被狼美人 {player.name} 魅惑而殉情")
    
    def check_game_over(self) -> Optional[Camp]:
        werewolves = self.get_werewolves()
        villagers = self.get_villagers()
        
        if not werewolves:
            self.game_winner = Camp.VILLAGER
            self.phase = GamePhase.GAME_OVER
            return Camp.VILLAGER
        
        if not villagers or len(werewolves) >= len(villagers):
            self.game_winner = Camp.WEREWOLF
            self.phase = GamePhase.GAME_OVER
            return Camp.WEREWOLF
        
        return None
    
    def reset_night_actions(self) -> None:
        self.werewolf_vote = None
        self.prophet_check = None
        self.witch_action = None
        self.guardian_protect = None
        self.night_kill_target = None
        self.wolf_beauty_charmed = None
    
    def get_visible_logs(self, player_id: int) -> List[GameLog]:
        visible_logs = []
        for log in self.logs:
            if log.public:
                visible_logs.append(log)
            elif player_id in log.visible_to:
                visible_logs.append(log)
        return visible_logs
