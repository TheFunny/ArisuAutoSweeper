from module.config.stored.classes import (
    StoredAP,
    StoredBase,
    StoredBountyTicket,
    StoredCounter,
    StoredExpiredAt0400,
    StoredExpiredAtMonday0400,
    StoredInt,
    StoredScrimmageTicket,
    StoredTacticalChallengeTicket,
)


# This file was auto-generated, do not modify it manually. To generate:
# ``` python -m module/config/config_updater.py ```

class StoredGenerated:
    AP = StoredAP("DataUpdate.ItemStorage.AP")
    Credit = StoredInt("DataUpdate.ItemStorage.Credit")
    Pyroxene = StoredInt("DataUpdate.ItemStorage.Pyroxene")
    BountyTicket = StoredBountyTicket("DataUpdate.ItemStorage.BountyTicket")
    ScrimmageTicket = StoredScrimmageTicket("DataUpdate.ItemStorage.ScrimmageTicket")
    TacticalChallengeTicket = StoredTacticalChallengeTicket("DataUpdate.ItemStorage.TacticalChallengeTicket")
