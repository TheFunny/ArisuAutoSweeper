from module.config.stored.classes import (
    StoredAP,
    StoredBase,
    StoredCounter,
    StoredExpiredAt0400,
    StoredExpiredAtMonday0400,
    StoredInt,
)


# This file was auto-generated, do not modify it manually. To generate:
# ``` python -m module/config/config_updater.py ```

class StoredGenerated:
    AP = StoredAP("DataUpdate.ItemStorage.AP")
    Credit = StoredInt("DataUpdate.ItemStorage.Credit")
    Pyroxene = StoredInt("DataUpdate.ItemStorage.Pyroxene")
