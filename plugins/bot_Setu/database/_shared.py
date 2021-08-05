from tinydb import TinyDB
from tinydb.storages import MemoryStorage

tmpDB = TinyDB(storage=MemoryStorage)
