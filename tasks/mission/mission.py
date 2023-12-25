from enum import Enum

from module.base.timer import Timer
from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.mission.ui import MissionUI, CommissionsUI
from tasks.stage.ap import AP
from tasks.cafe.cafe import Cafe
from tasks.circle.circle import Circle
from tasks.task.task import Task
from tasks.mail.mail import Mail
from tasks.item.data_update import DataUpdate
import json
import math
from filelock import FileLock
from datetime import datetime

class MissionStatus(Enum):
    AP = 0 # Calculate AP and decide to terminate Mission module or not
    NAVIGATE = 1 # Navigate to the stage page for example the commissions page or mission page
    SELECT = 2 # Select the stage mode for example hard or normal in mission
    ENTER = 3 # Search and for the stage in the stage list and enter
    SWEEP = 4 # Sweep the stage 
    RECHARGE = 5 # Recharge AP from other taks if they are enabled
    FINISH = -1 # Inidicate termination of Mission module


class Mission(MissionUI, CommissionsUI):
    _stage_ap = [10, 15, 15, 15]

    @property
    def stage_ap(self):
        return self._stage_ap

    @property
    def mission_info(self) -> list:
        """
        Read the config from MCE/config.json and extract the queue, a list of list. 
        If queue is empty repopulate from preferred template.

        Format of each element in queue: [mode, stage, sweep_num]
        e.g. ["N", "1-1", 3]

        Mode Acronyms:
            "N" : Normal Mission
            "H" : Hard Mission
            "E" : Event Quest
            "IR" : Item Retrieval / Commission where you get credit
            "BD" : Base Defense / Commission where you get exp

        Returns:
            list of list 
        """
        queue = []
        try:
            with open("MCE/config.json") as json_file:
                config_data = json.load(json_file)
            queue = config_data["Queue"]
            self.recharge_AP = config_data["RechargeAP"]
            self.reset_daily = config_data["ResetDaily"]
            self.reset_time = config_data["ResetTime"]
            self.last_run = config_data["LastRun"]
            self.event = config_data["Event"]
            if self.check_reset_daily() or not queue:
                preferred_template = config_data["PreferredTemplate"]
                queue = config_data["Templates"][preferred_template]
            if not self.event:
                queue = [x for x in queue if x[0] != "E"]
        except:
            logger.error("Failed to read configuration file")
        finally:
            return queue

    def check_reset_daily(self):
        # Check if it's time to reset the queue
        if self.reset_daily:
            current_datetime = datetime.now().replace(microsecond=0)  # Round to the nearest second
            current_date = current_datetime.date()
            current_time = current_datetime.time()
            last_run_datetime = datetime.strptime(self.last_run, "%Y-%m-%d %H:%M:%S")
            reset_time = datetime.strptime(self.reset_time, "%H:%M:%S").time()

            if current_date != last_run_datetime.date() and current_time >= reset_time:
                self.last_run = str(datetime.now().replace(microsecond=0))
                logger.info("Reset Daily activated.")
                return True
        return False
    
    @property
    def valid_task(self) -> list:
        task = self.mission_info
        if not task:
            logger.warning('Mission enabled but no task set')
            #self.error_handler()            
        return task

    @property
    def current_mode(self):
        return self.task[0][0]

    @property
    def current_stage(self):
        return self.task[0][1]

    @property
    def current_count(self):
        if self.current_mode == "H" and self.task[0][2] > 3:
            return 3
        return self.task[0][2] 

    @current_count.setter
    def current_count(self, value):
        self.task[0][2] = value
    
    def select(self) -> bool:
        """
        A wrapper method to select the current_mode 
        by calling the specific method based on its type.

        Return
            True if selection happens without any problem, False otherwise.
        """
        if self.current_mode in ["N", "H"]:
            return self.select_mission(self.current_mode, self.current_stage)
        elif self.current_mode in ["BD", "IR"]:
            return self.select_commission(self.current_mode)
        elif self.current_mode == "E":
            #return self.select_mode(SWITCH_QUEST)
            logger.error("Event not yet implemented")
            return False
        else:
            logger.error("Uknown mode")
            return False
        
    def get_realistic_count(self) -> int:
        """
        Calculate the possible number of sweeps based on the current AP
        """
        ap_cost = 20 if self.current_mode == "H" else 10
        required_ap = ap_cost * self.current_count
        return math.floor(min(required_ap, self.current_ap) / ap_cost)

    def update_task(self, failure=False):
        """
        Update self.task and save the current state of the queue in 
        MCE/config.json. 
        """
        try:
            if failure or self.current_count == self.realistic_count:
                self.previous_mode = self.current_mode
                self.task.pop(0)
            else:
                self.previous_mode = None
                self.current_count -= self.realistic_count
            with open("MCE/config.json", "r") as json_file:
                config_data = json.load(json_file)
            with open("MCE/config.json", "w") as json_file:
                config_data["Queue"] = self.task
                config_data["LastRun"] = self.last_run
                json.dump(config_data, json_file, indent=2)
        except:
            logger.error("Failed to save configuration")
            self.task = []

    def update_ap(self):
        ap_cost = 20 if self.current_mode == "H" else 10
        ap = self.config.stored.AP
        ap_old = ap.value
        ap_new = ap_old - ap_cost * self.realistic_count
        ap.set(ap_new, ap.total)
        logger.info(f'Set AP: {ap_old} -> {ap_new}')

    def recharge(self) -> bool:
        """
        Check if AP related modules such as cafe, circle, task, mail are enabled and run them if they are.
        task_call only works after the current task is finished so is not suitable.
        """
        cafe_reward = self.config.cross_get(["Cafe", "Scheduler", "Enable"]) and self.config.cross_get(["Cafe", "Cafe", "Reward"])
        circle = self.config.cross_get(["Circle", "Scheduler", "Enable"])
        task = self.config.cross_get(["Task", "Scheduler", "Enable"])
        mail = self.config.cross_get(["Mail", "Scheduler", "Enable"])
        ap_tasks = [(cafe_reward,Cafe), (circle, Circle), (task, Task), (mail, Mail)]
        modules = [x[1] for x in ap_tasks if x[0]]
        if not modules:
            logger.info("Recharge AP was enabled but no AP related modules were enabled")
            return False
        for module in modules:
            module(config=self.config, device=self.device).run()
        return True
        
    def handle_mission(self, status):
        match status:
            case MissionStatus.AP:
                if not self.task:
                    return MissionStatus.FINISH
                self.realistic_count = self.get_realistic_count()
                if self.realistic_count == 0 and self.recharge_AP:
                        self.recharge_AP = False
                        return MissionStatus.RECHARGE
                elif self.realistic_count == 0 and not self.recharge_AP:
                    return MissionStatus.FINISH
                else:
                    return MissionStatus.NAVIGATE
            case MissionStatus.NAVIGATE:      
                self.navigate(self.previous_mode, self.current_mode)
                return MissionStatus.SELECT
            case MissionStatus.SELECT:
                if self.select():
                    return MissionStatus.ENTER
                self.update_task(failure=True)
                return MissionStatus.AP
            case MissionStatus.ENTER:
                if self.enter_stage(self.current_stage):
                    return MissionStatus.SWEEP
                self.update_task(failure=True)
                return MissionStatus.AP
            case MissionStatus.SWEEP:
                if self.do_sweep(self.current_mode, self.realistic_count):
                    self.update_ap()
                    self.update_task()
                else:
                    self.update_task(failure=True)
                return MissionStatus.AP    
            case MissionStatus.RECHARGE:
                if self.recharge():
                    DataUpdate(config=self.config, device=self.device).run()
                    return MissionStatus.AP
                return MissionStatus.FINISH
            case MissionStatus.FINISH:
                return status
            case _:
                logger.warning(f'Invalid status: {status}')
        return status

    def run(self):
        self.lock = FileLock("MCE/config.json.lock")
        with self.lock.acquire():
            self.previous_mode = None
            self.task = self.valid_task
            action_timer = Timer(0.5, 1)
            status = MissionStatus.AP
            
            """Update the dashboard to accurately calculate AP"""
            DataUpdate(config=self.config, device=self.device).run()
            
            while 1:
                self.device.screenshot()

                if self.ui_additional():
                    continue

                if action_timer.reached_and_reset():
                    logger.attr('Status', status)
                    status = self.handle_mission(status)

                if status == MissionStatus.FINISH:
                    break

            self.config.task_delay(server_update=True)
        