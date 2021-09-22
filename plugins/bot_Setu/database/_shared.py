from tinydb import TinyDB
from tinydb.storages import MemoryStorage

tmpDB = TinyDB(storage=MemoryStorage)
freqLimitTable = tmpDB.table("freqLimit")
sentlistTable = tmpDB.table("sentlist")
