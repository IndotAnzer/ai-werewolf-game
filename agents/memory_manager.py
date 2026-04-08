from typing import List, Dict, Any
from datetime import datetime
from core.game_state import GameState, Player


class Memory:
    def __init__(self, content: str, memory_type: str = "observation", importance: int = 5):
        self.content = content
        self.memory_type = memory_type
        self.importance = importance
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "timestamp": self.timestamp.isoformat()
        }


class MemoryManager:
    def __init__(self, player: Player):
        self.player = player
        self.memories: List[Memory] = []
    
    def add_memory(self, content: str, memory_type: str = "observation", importance: int = 5) -> None:
        memory = Memory(content, memory_type, importance)
        self.memories.append(memory)
        self.player.memories.append(content)
    
    def get_recent_memories(self, limit: int = 10) -> List[Memory]:
        return sorted(self.memories, key=lambda m: m.timestamp, reverse=True)[:limit]
    
    def get_important_memories(self, min_importance: int = 7) -> List[Memory]:
        return [m for m in self.memories if m.importance >= min_importance]
    
    def get_memories_by_type(self, memory_type: str) -> List[Memory]:
        return [m for m in self.memories if m.memory_type == memory_type]
    
    def format_memories_for_prompt(self, limit: int = 20) -> str:
        recent = self.get_recent_memories(limit)
        if not recent:
            return "暂无记忆"
        
        formatted = []
        for i, memory in enumerate(reversed(recent), 1):
            formatted.append(f"{i}. [{memory.memory_type}] {memory.content}")
        
        return "\n".join(formatted)
    
    def record_game_event(self, game_state: GameState, event_description: str) -> None:
        self.add_memory(event_description, "game_event", 8)
    
    def record_observation(self, observation: str, importance: int = 5) -> None:
        self.add_memory(observation, "observation", importance)
    
    def record_suspicion(self, target_player_id: int, suspicion_level: str, reason: str) -> None:
        target = self.player
        content = f"对玩家{target_player_id}的怀疑程度：{suspicion_level}，原因：{reason}"
        self.add_memory(content, "suspicion", 7)
    
    def record_strategy(self, strategy: str) -> None:
        self.add_memory(strategy, "strategy", 9)
