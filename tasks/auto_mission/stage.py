from enum import Enum

class StageState(Enum):
    SUB = 0
    UNCLEARED = 1
    CLEARED = 2
    SSS = 3
    CHEST = 4

class Stage:
    def __init__(self, name: str, state: str, data: dict):
        self.name = name
        self.state = state
        self.data = data

    @property
    def formation_start_info(self):
        if self.state == StageState.SUB:
            return None
        return self.data["start"].items()
    
    @property
    def start_info(self):
        if self.state == StageState.SUB:
            return None
        return self.data["start"].values()
    
    @property
    def formation_info(self):
        if self.state == StageState.SUB:
            return self.data["SUB"]
        return self.data["start"].keys()
    
    @property
    def action_info(self):
        if self.state == StageState.SUB:
            return None
        return self.data["action"]