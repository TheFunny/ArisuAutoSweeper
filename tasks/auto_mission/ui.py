from module.logger import logger
from module.ocr.ocr import Digit
from tasks.auto_mission.stage import StageState, Stage
from tasks.auto_mission.copilot import Copilot
from tasks.stage.assets.assets_stage_sweep import ENTER #SWEEP
from tasks.auto_mission.assets.assets_auto_mission import *
import importlib

class AutoMissionUI(Copilot):
    """
    Class dedicated to navigate the mission page and check stages
    """
    def get_stages_data(self, mode, area):
        # Dynamically generate the complete module path
        if mode == "N":
            module_path = f'tasks.auto_mission.normal_task.normal_task_' + str(area)
        else:
            module_path = f'tasks.auto_mission.hard_task.hard_task_' + str(area)
        # Import the specified module
        try:
            stage_module = importlib.import_module(module_path)
            stage_data = getattr(stage_module, 'stage_data', None)
            # Get stage_data data from the module
            return stage_data
        except ModuleNotFoundError:
            logger.error(f"Exploration not supported for area {area}, under development...")
            return None

    def wait_mission_info(self, mode, open_task=False, max_retry=99999):
        """
        Wait for the task information popup to load
        @param self:
        @return:
        """
        while max_retry > 0:
            self.device.screenshot()
            # Main task
            if self.appear(ENTER):
                return 'main'
            # Side quest
            if mode == "N" and self.appear(ENTER_SUB):
                return 'side'
            # Open the task if needed
            if open_task:
                if mode == "N":
                    self.device.swipe((917, 220), (917, 552))
                    self.sleep(1)
                #click enter
                self.click(1118, 239)
                #self.sleep(1)
            max_retry -= 1
        logger.error("max_retry {0}".format(max_retry))
        return None
    
    def check_stage_state(self, mode, completion_level):
        """
        Check the current task type
        @param self:
        @return:
        """
        # Wait for the task information popup to load
        self.wait_mission_info(mode)
        self.sleep(1)
        self.device.screenshot()
        # Side quest
        if mode == "N" and self.appear(ENTER_SUB):
            return StageState.SUB
        # Hard main task - Can collect gifts
        if completion_level == 'three_stars_chest' and self.appear(CHEST):
            return StageState.CHEST
        # Main task - Three stars
        if self.match_color(THREE_STARS):
            return StageState.SSS
        # Not cleared
        if self.match_color(ONE_STAR):
            return StageState.CLEARED
        # Main task - Cleared
        return StageState.UNCLEARED
        
    def get_stage_info(self, stage_name, stage_state, stages_data, completion_level):
        possible_stages = []
        for stage in stages_data:
            if stage_name in stage:
                possible_stages.append(stage)
        if possible_stages:
            if stage_state == StageState.CHEST:
                for stage in possible_stages:
                    if "present" in stage:
                        return stages_data[stage]
            elif completion_level in ["three_stars", "three_stars_chest"]:
                for stage in possible_stages:
                    if "sss" in stage:
                        return stages_data[stage]
            elif completion_level in ["clear"]:
                for stage in possible_stages:
                    if not "sss" in stage and "present" not in stage:
                        return stages_data[stage]
            return stages_data[possible_stages[0]]
        return None
    
    def check_stages(self, mode, area, stages_data, completion_level):
        """
        Find the stage that needs to be battled
        @param self:
        @param region:
        @return:
        """
        stage_index = 1
        max_index = 4 if mode == "H" else 6
        while 1:
            # Wait for the task information to load
            stage_state = self.check_stage_state(mode, completion_level)
            logger.info("Current stage status: {0}".format(stage_state))
            # Not cleared side quest
            if stage_state == StageState.SUB:
                logger.warning("Uncleared SUB stage, starting battle...")
                #return stage_state
                return Stage("SUB", stage_state, stages_data[str(area)])            
            # Get the current stage
            stage_name = f"{area}-{stage_index}"
            stage_info = self.get_stage_info(stage_name, stage_state, stages_data, completion_level)
            if not stage_info:
                logger.error(f"Exploration not supported for the stage {stage_name}, under development...")
                return None
            # Not cleared main task
            if stage_state == StageState.UNCLEARED:
                logger.warning(f"{stage_name} Not cleared main stage, starting battle...")
                return Stage(stage_name, stage_state, stage_info)
            # Mode 2 ⭐️⭐️⭐️ or ⭐️⭐️⭐️ + box gift
            if completion_level in ["three_stars", "three_stars_chest"]:
                if stage_state == StageState.CHEST:
                    logger.warning(f"{stage_name} Found chest, starting battle...")
                    return Stage(stage_name, stage_state, stage_info)
                if stage_state != StageState.SSS:
                    logger.warning(f"{stage_name} Not three-star cleared, starting battle...")
                    return Stage(stage_name, stage_state, stage_info)
            # Click on the next stage
            logger.info(f"{stage_name} already meets specified completion level, searching for the next stage")
            self.click(1172, 358, interval=0)
            # Check if still in the same region
            stage_index += 1
            if stage_index >= max_index:
                self.sleep(1)
                self.device.screenshot()
                if area != Digit(OCR_AREA).ocr_single_line(self.device.image):
                    return None
    
    def start_stage(self, stage):
        # Click to start the task
        if stage.state == StageState.SUB:
            self.select_then_check(ENTER_SUB, MOBILIZE)
        else:
            self.select_then_check(ENTER, MISSION_INFO)
        # Wait for the map to load