from tasks.mission.mission import Mission
from tasks.mission.ui import SWITCH_NORMAL, SWITCH_HARD
from tasks.auto_mission.ui import AutoMissionUI
from enum import Enum

from module.base.timer import Timer
from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.item.data_update import DataUpdate

import re

class AutoMissionStatus(Enum):
    AP = 0 # Calculate AP and decide to terminate Auto-Mission module or not
    STAGES_DATA = 1
    NAVIGATE = 2 # Navigate to the area and select mode
    ENTER = 3 # Enter the first stage in the stage list
    CHECK = 4 # Check stages and find a stage that requires to be completed
    START = 5 # Start the stage
    FORMATION = 6 # Select units based on the types required by the stage
    FIGHT = 7 # Fight the stage
    END = 8
    FINISH = -1 # Indicate termination of Auto-Mission module

class AutoMission(AutoMissionUI, Mission):
    def __init__(self, config, device):
        super().__init__(config, device) 
        self.task = None
        self.previous_mode = None
        self.previous_area = None
        self._stage = None
        self.stages_data = None
        self.default_type_to_preset = self.get_default_type_to_preset()
        self.current_type_to_preset = None

    def get_default_type_to_preset(self):
        type_to_preset =  {
            "burst1": self.config.Formation_burst1,
            "burst2": self.config.Formation_burst2,
            "pierce1": self.config.Formation_pierce1,
            "pierce2": self.config.Formation_pierce2,
            "mystic1": self.config.Formation_mystic1,
            "mystic2": self.config.Formation_mystic2
        }
        valid = True

        for type, preset in type_to_preset.items():
            preset_list = []
            if isinstance(preset, str):
                preset = re.sub(r'[ \t\r\n]', '', preset)
                preset = preset.split("-")
                if len(preset) == 2:
                    column = preset[0]
                    row = preset[1]
                    if (column.isdigit() and 1 <= int(column) <= 4) and (row.isdigit() and 1 <= int(row) <= 5):
                        preset_list = [int(num) for num in preset]
            if not preset_list:
                logger.error(f"Failed to read {type}'s preset settings")
                valid = False
                continue
            type_to_preset[type] = preset_list

        if not valid:
            raise RequestHumanTakeover
        return type_to_preset
        
    def validate_area(self, mode, area_input):
        area_list = []
        if isinstance(area_input, str):
            area_input = re.sub(r'[ \t\r\n]', '', area_input)
            area_input = (re.sub(r'[＞﹥›˃ᐳ❯]', '>', area_input)).split('>')
            # tried to convert to set to remove duplicates but doesn't maintain order
            [area_list.append(x) for x in area_input if x not in area_list]    
        elif isinstance(area_input, int):
            area_list = [str(area_input)]

        if area_list and len([x for x in area_list if x.isdigit()]) == len(area_list):
            return area_list        

        mode_name = "Normal" if mode == "N" else "H"
        logger.error(f"Failed to read Mission {mode_name}'s area settings")
        return None
        
    def find_alternative(self, type, preset_list):
        if not self.config.Formation_Substitute:
            return None

        alternatives_dictionary = {
            'pierce1': ['pierce2', 'burst1', 'burst2', 'mystic1', 'mystic2'],
            'pierce2': ['burst1', 'burst2', 'mystic1', 'mystic2'],
            'burst1': ['burst2', 'pierce1', 'pierce2', 'mystic1', 'mystic2'],
            'burst2': ['pierce1', 'pierce2', 'mystic1', 'mystic2'],
            'mystic1': ['mystic2', 'burst1', 'burst2', 'pierce1', 'pierce2'],
            'mystic2': ['burst1', 'burst2', 'pierce1', 'pierce2'],
        }
        alternatives = alternatives_dictionary[type]
        for alternative in alternatives:
            alternative_preset = self.default_type_to_preset[alternative]
            if alternative_preset not in preset_list:
                preset_list.append(alternative_preset)
                logger.warning(f"{type} was replaced by {alternative}")
                return preset_list
        logger.error(f"Unable to find replacements for {type}")
        return None
            
    @property
    def mission_info(self) -> list:
        valid = True
        mode = ("N", "H")
        enable = (self.config.Normal_Enable, self.config.Hard_Enable)
        area = (self.config.Normal_Area, self.config.Hard_Area)
        area_list = [None, None]
        completion_level = (self.config.Normal_Completion, self.config.Hard_Completion)
        for index in range(2):
            if enable[index]:
                area_list[index] = self.validate_area(mode[index], area[index]) 
                valid = valid if area_list[index] else False
        if valid:
            info = zip(mode, area_list, completion_level)
            return list(filter(lambda x: x[1], info))
        return None

    @property
    def current_mode(self):
        return self.task[0][0]

    @property
    def current_area(self):
        return int(self.task[0][1][0])
    
    @property
    def current_stage(self):
        return self._stage
    
    @current_stage.setter
    def current_stage(self, value):
        self._stage = value
    
    @property
    def current_completion_level(self):
        return self.task[0][2]
    
    @property
    def current_count(self):
        return 1
    
    def update_stages_data(self):
        if [self.previous_mode, self.previous_area] != [self.current_mode, self.current_area]:
            self.stages_data = self.get_stages_data(self.current_mode, self.current_area)
        if self.stages_data:
            return True
        return False
    
    def update_current_type_to_preset(self):
        if [self.previous_mode, self.previous_area] == [self.current_mode, self.current_area]:
            self.current_type_to_preset = None
            return True
        
        mode_name = "Normal" if self.current_mode == "N" else "Hard"
        use_alternative = False
        for stage, info in self.stages_data.items():
            if "start" not in info:
                continue

            list_preset = []
            list_type = []
            for type in info["start"]:
                preset = self.default_type_to_preset[type]
                list_type.append(type)

                if preset not in list_preset:
                    list_preset.append(preset)
                    continue
                logger.error(f"Mission {mode_name} {self.current_area} requires {list_type} but they are both set to preset {preset}")
                list_preset = self.find_alternative(type, list_preset)
                use_alternative = True
                if list_preset:
                    continue                
                return False

            if use_alternative:
                d = {}
                for index in range(len(list_type)):
                    type, preset = list_type[index],  list_preset[index]
                    d[type] = preset
                self.current_type_to_preset = d
            else:
                self.current_type_to_preset = self.default_type_to_preset
            return True
        
        return False
    
    def update_task(self):
        self.previous_mode = self.current_mode
        self.previous_area = self.current_area
        area_list = self.task[0][1]
        area_list.pop(0)
        if not area_list:
            self.task.pop(0)
        
    def handle_auto_mission(self, status):
        match status:
            case AutoMissionStatus.AP:
                if self.task:
                    self.realistic_count = self.get_realistic_count()
                    if self.realistic_count != 0:
                        return AutoMissionStatus.STAGES_DATA
                return AutoMissionStatus.FINISH
            
            case AutoMissionStatus.STAGES_DATA:
                if self.update_stages_data() and self.update_current_type_to_preset():
                    return AutoMissionStatus.NAVIGATE
                return AutoMissionStatus.END
            
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
                self.current_stage = self.check_stages(self.current_mode, self.current_area, self.stages_data, self.current_completion_level)
                if self.current_stage:
                    return AutoMissionStatus.START
                return AutoMissionStatus.END

            case AutoMissionStatus.START:
                self.start_stage(self.current_stage)
                return AutoMissionStatus.FORMATION
                                
            case AutoMissionStatus.FORMATION:
                self.formation(self.current_stage, self.current_type_to_preset)
                return AutoMissionStatus.FIGHT
            
            case AutoMissionStatus.FIGHT:
                self.fight(self.current_stage, manual_boss=self.config.ManualBoss_Enable)
                self.update_ap()
                self.previous_mode = self.current_mode
                self.previous_area = self.current_area
                return AutoMissionStatus.AP

            case AutoMissionStatus.END:
                self.update_task()
                return AutoMissionStatus.AP
                        
            case AutoMissionStatus.FINISH:
                return status
            
            case _:
                logger.warning(f'Invalid status: {status}')

        return status

    def run(self):
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
        