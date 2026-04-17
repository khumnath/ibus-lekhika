import gi
gi.require_version('IBus', '1.0')
from gi.repository import IBus

table = IBus.LookupTable.new(10, 0, True, True)
print(dir(table))
