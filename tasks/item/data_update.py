from module.base.timer import Timer
from module.logger import logger
from module.ocr.ocr import Digit, DigitCounter
from tasks.base.page import page_work
from tasks.base.ui import UI
from tasks.item.assets.assets_item_data import *


class DataUpdate(UI):
    def _get_data(self):
        """
        Page:
            in: page_work
        """
        ap = DigitCounter(OCR_AP).ocr_single_line(self.device.image)
        # Data for Credit and Pyroxene
        ocr = Digit(OCR_DATA)
        timeout = Timer(2, count=6).start()
        while 1:
            data = ocr.detect_and_ocr(self.device.image)
            if len(data) != 2:
                data = [data[0], data[-1]]
            logger.attr('Data', data)
            credit, pyroxene = [int(''.join([v for v in d.ocr_text if v.isdigit()])) for d in data]
            if credit > 0 or pyroxene > 0:
                break

            logger.warning(f'Invalid credit and pyroxene: {data}')
            if timeout.reached():
                logger.warning('Get data timeout')
                break

        logger.attr('Credit', credit)
        logger.attr('Pyroxene', pyroxene)
        with self.config.multi_set():
            self.config.stored.AP.set(ap[0], ap[2])
            self.config.stored.Credit.value = credit
            self.config.stored.Pyroxene.value = pyroxene

        return ap, credit, pyroxene

    def run(self):
        self.ui_ensure(page_work, acquire_lang_checked=False)

        with self.config.multi_set():
            self._get_data()
            self.config.task_delay(server_update=True)
