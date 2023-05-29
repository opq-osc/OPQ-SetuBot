import time

from botoy import contrib, logger, scheduler
from tinydb import where
from tinyrecord import transaction

from ._shared import revokeTable


@contrib.to_async
def saveMsgSeq(botqq: int, group: int, msgseq: int, revoke_time: int, time: int):
    if revoke_time == 0:
        logger.info(f"群{group}未开启撤回")
        return
    with transaction(revokeTable) as tr:
        with tr.lock:
            tr.insert(
                {
                    "group": group,
                    "botqq": botqq,
                    "msgseq": msgseq,
                    "revoketime": revoke_time,
                    "time": time

                }
            )
            logger.info(f"bot:{botqq} 群{group} msgseq:{msgseq} 撤回时间:{revoke_time}")


@contrib.to_async
def getRevokeTime(botqq: int, group: int, msgseq: int):
    with transaction(revokeTable) as tr:
        with tr.lock:
            if data := revokeTable.get(
                    (where("group") == group) & (where("botqq") == botqq) & (where("msgseq") == msgseq)):  # 如果有数据
                revokeTable.remove(doc_ids=[data.doc_id])
                return data["revoketime"]
            else:
                return None


def del_miss_data():
    logger.warning("检查未使用的msgseq")
    with transaction(revokeTable) as tr:
        with tr.lock:
            if data := revokeTable.all():  # 如果有数据
                miss_seqs = []
                for d in data:
                    if int(time.time()) - d["time"] >= 120:
                        miss_seqs.append(d.doc_id)
                tr.remove(doc_ids=miss_seqs)
                logger.warning(f"移除{len(miss_seqs)}个未使用msgseq")


scheduler.add_job(
    del_miss_data,
    "cron",
    minute="*/10",
    # second="*/10",
    misfire_grace_time=30,
)  # 10分钟检查一次数据库是否有没被删除的seq
