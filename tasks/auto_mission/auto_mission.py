from tasks.mission.mission import Mission
from tasks.mission.ui import SWITCH_NORMAL, SWITCH_HARD
from tasks.auto_mission.ui import AutoMissionUI
from enum import Enum

from module.base.timer import Timer
from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.item.data_update import DataUpdate
from module.base.decorator import cached_property

class AutoMissionStatus(Enum):
    AP = 0 # Calculate AP and decide to terminate Auto-Mission module or not
    NAVIGATE = 1 # Navigate to the area and select mode
    ENTER = 2 # Enter the first stage in the stage list
    CHECK = 3 # Check stages and find a stage that requires to be completed
    START = 4 # Start the stage
    FORMATION = 5 # Select units based on the types required by the stage
    FIGHT = 6 # Fight the stage
    FINISH = -1 # Indicate termination of Auto-Mission module

class AutoMission(AutoMissionUI, Mission):
    @property
    def mission_info(self) -> list:
        valid = True
        mode = ("N", "H")
        enable = (self.config.Normal_Enable, self.config.Hard_Enable)
        area = (self.config.Normal_Area, self.config.Hard_Area)
        stages_data = [None, None]
        completion_level = (self.config.Normal_Completion, self.config.Hard_Completion)
        for index in range(2):
            if enable[index]:
                stages_data[index] = self.get_stages_data(mode[index], area[index]) 
                valid = valid if self.check_formation(mode[index], area[index], stages_data[index]) else False
        if valid:
            info = zip(mode, area, stages_data, completion_level)
            return list(filter(lambda x: x[2], info))
    
    def check_formation(self, mode, area, stages_data):
        mode_name = "Normal" if mode == "N" else "Hard"
        if stages_data:
            for stage, info in stages_data.items():
                if "start" in info:
                    types = info["start"]
                    list_unit = []
                    list_type = []
                    for type in types:
                        list_type.append(type)
                        unit = self.type_to_unit[type]
                        if unit in list_unit:
                            logger.error(f"Mission {mode_name} {area} requires {list_type} but they are both set to unit {unit}")
                            return False
                        list_unit.append(unit)
                        if list_unit and list_unit[0] > unit:
                            logger.error(f"Mission {mode_name} {area} requires {list_type} but they are set to units {list_unit} respectively.\
                                         Due to Auto-Mission's implementation, the first unit's index must be smaller than the second unit's index.")
                            return False
                    return True
        return False

    @cached_property
    def type_to_unit(self):
        return {
            "burst1": self.config.Formation_burst1,
            "burst2": self.config.Formation_burst2,
            "pierce1": self.config.Formation_pierce1,
            "pierce2": self.config.Formation_pierce2,
            "mystic1": self.config.Formation_mystic1,
            "mystic2": self.config.Formation_mystic2
        }

    @property
    def current_mode(self):
        return self.task[0][0]

    @property
    def current_area(self):
        return self.task[0][1]
    
    @property
    def current_stage(self):
        return self._stage
    
    @current_stage.setter
    def current_stage(self, value):
        self._stage = value
    
    @property
    def current_stages_data(self):
        return self.task[0][2]
    
    @property
    def current_completion_level(self):
        return self.task[0][3]
    
    @property
    def current_count(self):
        return 1
    
    def update_task(self):
        self.task.pop(0)
        
    def handle_auto_mission(self, status):
        match status:
            case AutoMissionStatus.AP:
                if self.task:
                    self.realistic_count = self.get_realistic_count()
                    if self.realistic_count != 0:
                        return AutoMissionStatus.NAVIGATE
                return AutoMissionStatus.FINISH
            
            case AutoMissionStatus.NAVIGATE: 
                switch = SWITCH_NORMAL if self.current_mode == "N" else SWITCH_HARD
                self.navigate(self.previous_mode, self.current_mode)
                if self.select_area(self.current_area) and self.select_mode(switch):
                    return AutoMissionStatus.ENTER
                raise RequestHumanTakeover
            
            case AutoMissionStatus.ENTER:
                if self.wait_mission_info(self.current_mode, open_task=True):
                    return AutoMissionStatus.CHECK
                raise RequestHumanTakeover
            
            case AutoMissionStatus.CHECK:
                self.current_stage = self.check_stages(*self.task[0])
                if self.current_stage:
                    return AutoMissionStatus.START
                self.update_task()
                return AutoMissionStatus.AP

            case AutoMissionStatus.START:
                self.start_stage(self.current_stage)
                return AutoMissionStatus.FORMATION
                                
            case AutoMissionStatus.FORMATION:
                self.formation(self.current_stage, self.type_to_unit)
                return AutoMissionStatus.FIGHT
            
            case AutoMissionStatus.FIGHT:
                self.fight(self.current_stage, manual_boss=self.config.ManualBoss_Enable)
                # Return to the previous region to prevent map unlock card recognition
                self.select_area(self.current_area - 1)
                self.update_ap()
                self.previous_mode = self.current_mode
                return AutoMissionStatus.AP
                        
            case AutoMissionStatus.FINISH:
                return status
            
            case _:
                logger.warning(f'Invalid status: {status}')

        return status

    def run(self):
        self.previous_mode = None
        self._stage = None
        self.task = self.valid_task
        if self.task:
            action_timer = Timer(0.5, 1)
            status = AutoMissionStatus.AP
            
            """Update the dashboard to accurately calculate AP"""
            DataUpdate(config=self.config, device=self.device).run()
            
            while 1:
                self.device.screenshot()

                if self.ui_additional():
                    continue

                if action_timer.reached_and_reset():
                    logger.attr('Status', status)
                    status = self.handle_auto_mission(status)

                if status == AutoMissionStatus.FINISH:
                    break
        else:
            raise RequestHumanTakeover
        
        self.config.task_delay(server_update=True)
        