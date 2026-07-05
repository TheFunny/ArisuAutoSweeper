from module.base.base import ModuleBase
from module.logger import logger


class AP(ModuleBase):
    _stage = 0

    @property
    def stage(self) -> int:
        return self._stage

    @classmethod
    def set_stage(cls, stage: int):
        cls._stage = stage

    @property
    def stage_ap(self) -> int | list:
        """
        To be redefined in subclass.

        Returns:
            Task ap
        """
        return 0

    @property
    def current_ap(self):
        return self.config.stored.AP.value

    def update_ap(self, count: int, stage: int = None):
        ap = self.config.stored.AP
        ap_old = ap.value
        ap_new = ap_old - self.stage_ap_cost(stage) * count
        ap.set(ap_new, ap.total)
        logger.info(f'Set AP: {ap_old} -> {ap_new}')

    def stage_ap_cost(self, stage: int = None) -> int:
        if isinstance(self.stage_ap, int):
            return self.stage_ap
        if isinstance(self.stage_ap, list):
            if not stage:
                stage = self.stage if self.stage else len(self.stage_ap)
            return self.stage_ap[stage - 1]

    def is_ap_enough(self, count: int, stage: int = None) -> bool:
        cost = self.stage_ap_cost(stage) * count
        logger.info(f'Check AP: {self.current_ap} / {cost}')
        return self.current_ap >= cost
