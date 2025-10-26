from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class PetStats:
    hambre: int
    energía: int
    felicidad: int
    salud: int
    max_energía: int
    max_salud: int

@dataclass
class PetSkill:
    name: str
    description: str
    battle_effect: Optional[Dict]
    element: Optional[str]
    unlocked_at: int  # Nivel de desbloqueo

@dataclass
class Pet:
    name: str
    tipo: str
    clase: str
    elemento: str
    emoji: str
    nivel: int
    experiencia: int
    stats: PetStats
    estado: str
    última_interacción: str
    habilidades: List[PetSkill]
    inventario: List[Dict]
    
    def to_dict(self):
        data = asdict(self)
        data['stats'] = asdict(self.stats)
        data['habilidades'] = [asdict(skill) for skill in self.habilidades]
        return data
    
    @classmethod
    def from_dict(cls, data):
        stats = PetStats(**data['stats'])
        habilidades = [PetSkill(**skill) for skill in data.get('habilidades', [])]
        data['stats'] = stats
        data['habilidades'] = habilidades
        return cls(**data)

@dataclass
class UserPets:
    user_id: str
    mascotas: Dict[str, Pet]  # name -> Pet
    misiones: Dict = None
    last_updated: str = None
    
    def __post_init__(self):
        if self.misiones is None:
            self.misiones = {}
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()
    
    def to_dict(self):
        data = asdict(self)
        data['mascotas'] = {name: pet.to_dict() for name, pet in self.mascotas.items()}
        return data
    
    @classmethod
    def from_dict(cls, data):
        mascotas = {name: Pet.from_dict(pet_data) for name, pet_data in data.get('mascotas', {}).items()}
        data['mascotas'] = mascotas
        return cls(**data)