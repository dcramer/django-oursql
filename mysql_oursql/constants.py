# I don't believe these change, and oursql doesn't include them in the same way as
# MySQLdb does
class FIELD_TYPE:
    BLOB = 252
    CHAR = 1
    DECIMAL = 0
    NEWDECIMAL = 246
    DATE = 10
    DATETIME = 12
    DOUBLE = 5
    FLOAT = 4
    INT24 = 9
    LONG = 3
    LONGLONG = 8
    SHORT = 2
    STRING = 254
    TIMESTAMP = 7
    TINY = 1
    TINY_BLOB = 249
    MEDIUM_BLOB = 250
    LONG_BLOB = 251
    VAR_STRING = 253
    
    # gis constants
    GEOMETRY = 255