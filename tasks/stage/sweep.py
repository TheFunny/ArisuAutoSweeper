from enum import Enum

from module.base.base import ModuleBase
from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Digit
from tasks.stage.assets.assets_stage_sweep import *


class SweepStatus(Enum):
    SELECT = 1
    START = 2
    CONFIRM = 3
    SKIP = 4
    END = 5
    FINISH = 6


class StageSweep:
    def __init__(
            self,
            name: str,
            max_sweep: int,
    ):
        self.name = name
        self.sweep_num = None

        self.check: ButtonWrapper = None
        self.num: Digit = None
        self.plus: ButtonWrapper = None
        self.minus: ButtonWrapper = None
        self.max: ButtonWrapper = None
        self.min: ButtonWrapper = None
        self.sweep: ButtonWrapper = None
        self.sweep_confirm: ButtonWrapper = None
        self.enter: ButtonWrapper = None
        self.exit: ButtonWrapper = None
        self.skip_skip: ButtonWrapper = None
        self.skip_ok_upper: ButtonWrapper = None
        self.skip_ok_lower: ButtonWrapper = None
        self.set_button()

        self.min_sweep = 1
        self.max_sweep = max_sweep
        self.current_sweep = 0

        self.sweep_method = None

    def __str__(self):
        return f'StageSweep({self.name})'

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    def set_button(
            self,
            button_check: ButtonWrapper = None,
            button_num: ButtonWrapper = None,
            button_plus: ButtonWrapper = None,
            button_minus: ButtonWrapper = None,
            button_max: ButtonWrapper = None,
            button_min: ButtonWrapper = None,
            button_sweep: ButtonWrapper = None,
            button_sweep_confirm: ButtonWrapper = None,
            button_enter: ButtonWrapper = None,
            button_exit: ButtonWrapper = None,
            button_skip_skip: ButtonWrapper = None,
            button_skip_ok_upper: ButtonWrapper = None,
            button_skip_ok_lower: ButtonWrapper = None,
    ):
        self.check = button_check if button_check else CHECK_SWEEP
        self.num = Digit(button_num if button_num else OCR_NUM)
        self.plus = button_plus if button_plus else PLUS
        self.minus = button_minus if button_minus else MINUS
        self.max = button_max if button_max else MAX
        self.min = button_min if button_min else MIN
        self.sweep = button_sweep if button_sweep else SWEEP
        self.sweep_confirm = button_sweep_confirm if button_sweep_confirm else SWEEP_CONFIRM
        self.enter = button_enter if button_enter else ENTER
        self.exit = button_exit if button_exit else EXIT
        self.skip_skip = button_skip_skip if button_skip_skip else SKIP_SKIP
        self.skip_ok_upper = button_skip_ok_upper if button_skip_ok_upper else SKIP_OK_UPPER
        self.skip_ok_lower = button_skip_ok_lower if button_skip_ok_lower else SKIP_OK_LOWER

    def set_mode(self, mode: str = None, num: int = None) -> bool:
        if num is not None:
            self.sweep_num = num
            match num:
                case 0:
                    self.sweep_method = self.set_sweep_min
                case -1:
                    self.sweep_method = self.set_sweep_max
                case x if x > 0:
                    self.sweep_method = self.set_sweep_num
                case _:
                    logger.warning(f'Invalid sweep num: {num}')
            return True
        if mode is not None:
            match mode:
                case 'max':
                    self.sweep_method = self.set_sweep_max
                case 'min':
                    self.sweep_method = self.set_sweep_min
                case _:
                    logger.warning(f'Invalid sweep mode: {mode}')
            return True
        logger.warning(f'Invalid sweep setting')
        return False

    def check_sweep(self, main: ModuleBase):
        return main.appear(self.check)

    def check_skip(self, main: ModuleBase):
        return main.appear(self.skip_skip) or main.appear(self.skip_ok_upper) or main.appear(self.skip_ok_lower)

    def load_sweep_num(self, main: ModuleBase):
        self.current_sweep = self.num.ocr_single_line(main.device.image)

    def set_sweep_num(self, main: ModuleBase, skip_first_screenshot=True) -> bool:
        num = self.sweep_num
        if num < self.min_sweep or num > self.max_sweep:
            logger.warning(f'Invalid sweep num: {num}')
            return False
        logger.info(f'Set sweep num: {num}')
        retry = Timer(1, 2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            self.load_sweep_num(main)

            if self.current_sweep == num:
                logger.info(f'Sweep num reaches {num}')
                return True
            elif self.current_sweep == 0:
                logger.info(f'Current sweep num is 0')
                return False

            if retry.reached_and_reset():
                diff = num - self.current_sweep
                button = self.plus if diff > 0 else self.minus
                main.device.multi_click(button, abs(diff), interval=(0.2, 0.3))

    def set_sweep_max(self, main: ModuleBase, skip_first_screenshot=True):
        logger.info(f'Set sweep max: {self.max_sweep}')
        retry = Timer(1, 2)
        count = 0
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            self.load_sweep_num(main)

            if self.current_sweep == self.max_sweep:
                logger.info(f'Sweep max reaches {self.max_sweep}')
                return True
            elif count == 1 and self.current_sweep != 1:
                logger.info("Set sweep max")
                return True
            elif self.current_sweep == 0:
                logger.info(f'Current sweep num is 0')
                return False

            if retry.reached_and_reset():
                main.click_with_interval(self.max, interval=0)
                count += 1
                continue

            if count > 2:
                logger.info("Set sweep max")
                return True

    def set_sweep_min(self, main: ModuleBase, skip_first_screenshot=True):
        logger.info(f'Set sweep min: {self.min_sweep}')
        retry = Timer(1, 2)
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            self.load_sweep_num(main)

            if self.current_sweep == self.min_sweep:
                logger.info(f'Sweep min reaches {self.min_sweep}')
                return True
            elif self.current_sweep == 0:
                logger.info(f'Current sweep num is 0')
                return False

            if retry.reached_and_reset():
                main.click_with_interval(self.min, interval=0)

    def do_sweep(self, main: ModuleBase, mode: str = None, num: int = None, skip_first_screenshot=True) -> bool:
        if not self.set_mode(mode, num):
            return False
        timer = Timer(0.5, 1)
        timer_stable = Timer(1, 1).start()
        status = SweepStatus.SELECT
        while 1:
            if not timer_stable.reached():
                continue

            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                main.device.screenshot()

            if timer.reached_and_reset():
                logger.attr("Status", status)
                match status:
                    case SweepStatus.SELECT:
                        if self.sweep_method(main, skip_first_screenshot):
                            status = SweepStatus.START
                        else:
                            return False
                    case SweepStatus.START:
                        main.appear_then_click(self.sweep, interval=1)
                        if main.appear(self.sweep_confirm):
                            status = SweepStatus.CONFIRM
                    case SweepStatus.CONFIRM:
                        main.appear_then_click(self.sweep_confirm, interval=1)
                        if self.check_skip(main):
                            status = SweepStatus.SKIP
                    case SweepStatus.SKIP:
                        main.appear_then_click(self.skip_skip)
                        main.appear_then_click(self.skip_ok_upper)
                        main.appear_then_click(self.skip_ok_lower)
                        if self.check_sweep(main):
                            status = SweepStatus.END
                    case SweepStatus.END:
                        main.appear_then_click(self.exit, interval=1)
                        if not main.appear(self.check):
                            status = SweepStatus.FINISH
                    case SweepStatus.FINISH:
                        pass
                    case _:
                        logger.warning(f'Invalid status: {status}')
                        return False

            if status == SweepStatus.FINISH:
                logger.info(f'Sweep finish')
                return True
