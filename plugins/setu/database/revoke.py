import time

from botoy import contrib, logger
from tinydb import where
from tinyrecord import transaction

from ._shared import revokeTable


@contrib.to_async
def saveMsgSeq(group: int, msgseq: int, revoke_time: int):
    if revoke_time == 0:
        logger.info(f"群{group}未开启撤回")
        return
    with transaction(revokeTable) as tr:
        with tr.lock:
            tr.insert(
                {
                    "group": group,
                    "msgseq": msgseq,
                    "revoketime": revoke_time

                }
            )
            logger.info(f"群{group} msgseq:{msgseq} 撤回时间:{revoke_time}")


@contrib.to_async
def getRevokeTime(group: int, msgseq: int):
    with transaction(revokeTable) as tr:
        with tr.lock:
            if data := revokeTable.get((where("group") == group) & (where("msgseq") == msgseq)):  # 如果有数据
                revokeTable.remove(doc_ids=[data.doc_id])
                return data["revoketime"]
            else:
                return None
