from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime

class UserProfile:
    def __init__(self, user_id: str, username: str, coins: int, total_xp: int):
        self.user_id = user_id
        self.username = username
        self.coins = coins
        self.total_xp = total_xp

@dataclass
class UserProfile:
    user_id: str
    username: str
    coins: int = 0
    total_xp: int = 0
    created_at: str = None
    last_active: str = None
    achievements: Dict = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.last_active is None:
            self.last_active = datetime.now().isoformat()
        if self.achievements is None:
            self.achievements = {}
    
    def to_dict(self):
        return asdict(self)

@dataclass
class UserSession:
    user_id: str
    session_start: str
    session_end: Optional[str] = None
    commands_used: int = 0
    pets_interacted: int = 0
    
    def to_dict(self):
        return asdict(self)
    
@dataclass
class UserAchievement:
    name: str
    description: str
    date_earned: str
    points: int

    def to_dict(self):
        return asdict(self)