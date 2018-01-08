"""Contains functionality for converting DB2 catalog results into
Singer schemas."""
from singer.catalog import Schema

# https://www.ibm.com/support/knowledgecenter/ssw_ibm_i_71/db2/rbafzch2num.htm
BYTES_FOR_INTEGER_TYPE = {
    "smallint": 2,
    "integer": 4,
    "bigint": 8,
}
FLOAT_TYPES = {
    "float",
    "decfloat",
}
DECIMAL_TYPES = {
    "decimal",
    "numeric",
}

# https://www.ibm.com/support/knowledgecenter/ssw_ibm_i_71/db2/rbafzcharstrg.htm
STRING_TYPES = {
    "char",
    "varchar",
}

# https://www.ibm.com/support/knowledgecenter/ssw_ibm_i_71/db2/rbafzch2datetime.htm
DATETIME_TYPES = {
    "date",
    "timestmp",
    "time",
}

# Parent article for data types:
# https://www.ibm.com/support/knowledgecenter/ssw_ibm_i_71/db2/rbafzch2data.htm
def _for_column(col, pk_columns):
    data_type = col.data_type.lower()
    inclusion = "available"
    if col.column_name.lower() in [x.lower() for x in pk_columns]:
        inclusion = "automatic"
    result = Schema(inclusion=inclusion)
    if data_type in BYTES_FOR_INTEGER_TYPE:
        result.type = ["null", "integer"]
        bits = BYTES_FOR_INTEGER_TYPE[data_type] * 8
        result.minimum = 0 - 2 ** (bits - 1)
        result.maximum = 2 ** (bits - 1) - 1
    elif data_type in FLOAT_TYPES:
        result.type = ["null", "number"]
    elif data_type in DECIMAL_TYPES:
        if col.numeric_scale == 0:
            result.type = ["null", "integer"]
        else:
            result.type = ["null", "number"]
            result.multipleOf = 10 ** (0 - col.numeric_scale)
        result.exclusiveMaximum = True
        result.maximum = 10 ** (col.numeric_precision - col.numeric_scale)
        result.exclusiveMinimum = True
        result.minimum = -10 ** (col.numeric_precision - col.numeric_scale)
    elif data_type in STRING_TYPES:
        result.type = ["null", "string"]
        if col.character_maximum_length > 0:
            result.maxLength = col.character_maximum_length
    elif data_type in DATETIME_TYPES:
        result.type = ["null", "string"]
        result.format = "date-time"
    else:
        err = "Unsupported data type {}".format(data_type)
        result = Schema(None, inclusion="unsupported", description=err)
    return result


def generate(columns, pk_columns):
    properties = {c.column_name: _for_column(c, pk_columns) for c in columns}
    return Schema(type="object", properties=properties)
