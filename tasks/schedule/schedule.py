from enum import Flag

from module.base.timer import Timer
from module.exception import RequestHumanTakeover
from module.logger import logger
from tasks.base.assets.assets_base_page import BACK
from tasks.base.page import page_schedule
from tasks.schedule.ui import ScheduleUI
from tasks.base.assets.assets_base_page import SCHEDULE_CHECK

import re

class ScheduleStatus(Flag):
    OCR = 0
    ENTER = 1
    SELECT = 2
    END = 3
    FINISH = 4


class Schedule(ScheduleUI):    
    @property
    def schedule_info(self):
        info = []
        input_valid = True
        schedule_config = self.config.cross_get("Schedule")
        choices = ["Choice1", "Choice2", "Choice3", "Choice4", "Choice5"]

        for choice in choices:
            location, classrooms = schedule_config[choice]["Location"], schedule_config[choice]["Classrooms"]
            if location == "None" or not classrooms or (isinstance(classrooms, str) and classrooms.replace(" ", "") == ""):
                continue
            elif isinstance(classrooms, int):
                classrooms_list = [str(classrooms)]
            else:
                classrooms = classrooms.strip()
                classrooms = re.sub(r'[ \t\r\n]', '', classrooms)
                classrooms = (re.sub(r'[＞﹥›˃ᐳ❯]', '>', classrooms)).split('>')
                classrooms_list = []
                # tried to convert to set to remove duplicates but doesn't maintain order
                [classrooms_list.append(x) for x in classrooms if x not in classrooms_list]
            
            if self.valid_classroom(classrooms_list):
                info.append([location, classrooms_list])
            else:
                logger.error(f"Failed to read {choice}")
                input_valid = False

        return info if input_valid else []

    def valid_classroom(self, classrooms_list):
        if not classrooms_list:
            return False
        for classroom in classrooms_list:
            if not classroom.isdigit():
                return False
            if not 1 <= int(classroom) <= 9:
                return False
        return True
    
    @property
    def valid_task(self) -> list:
        task = self.schedule_info
        if not task:
            logger.warning('Lessons enabled but no task set')
            self.error_handler()
        return task

    def error_handler(self):
        action = self.config.Schedule_OnError
        if action == 'stop':
            raise RequestHumanTakeover
        elif action == 'skip':
            with self.config.multi_set():
                self.config.task_delay(server_update=True)
                self.config.task_stop()

    @property
    def current_location(self):
        return self.task[0][0]

    @property
    def current_classrooms(self):
        return self.task[0][1]

    def handle_schedule(self, status):
        match status:
            case ScheduleStatus.OCR:
                if self.task:
                    self.ticket = self.get_ticket()
                    if self.ticket not in [0, None]:
                        return ScheduleStatus.ENTER
                return ScheduleStatus.FINISH
            case ScheduleStatus.ENTER:
                if self.enter_location(self.current_location):
                    return ScheduleStatus.SELECT
                else:
                    self.error_handler()
            case ScheduleStatus.SELECT:
                if self.select_classrooms(self.ticket, self.current_classrooms):
                    self.task.pop(0)
                    return ScheduleStatus.END
                return ScheduleStatus.FINISH
            case ScheduleStatus.END:
                if self.appear(SCHEDULE_CHECK):
                    return ScheduleStatus.OCR
                self.click_with_interval(BACK, interval=2)
            case ScheduleStatus.FINISH:
                return status
            case _:
                logger.warning(f'Invalid status: {status}')
        return status

    def run(self):
        self.ui_ensure(page_schedule)
        self.task = self.valid_task
        self.set_clickx()
        action_timer = Timer(0.5, 1)
        status = ScheduleStatus.OCR

        while 1:
            self.device.screenshot()

            if self.ui_additional():
                continue

            if action_timer.reached_and_reset():
                logger.attr('Status', status)
                status = self.handle_schedule(status)

            if status == ScheduleStatus.FINISH:
                break

        self.config.task_delay(server_update=True)