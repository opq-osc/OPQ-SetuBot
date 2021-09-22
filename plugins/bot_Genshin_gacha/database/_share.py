from pathlib import Path

from tinydb import TinyDB
from tinydb.storages import MemoryStorage

curFileDir = Path(__file__).parent  # 当前文件路径

tmpDB = TinyDB(storage=MemoryStorage)
gachaDB = TinyDB(curFileDir / "DB" / "gachaData.json", indent=4, ensure_ascii=False)
