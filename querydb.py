from sqlalchemy  import create_engine, MetaData, Table, select # type: ignore
import pandas as pd

def query_database():
    DATABASE_TYPE = 'mysql'
    DBAPI = 'CONFIDENTIAL'
    HOST = 'CONFIDENTIAL'
    USER = 'CONFIDENTIAL'
    PASSWORD = 'CONFIDENTIAL'
    DATABASE = 'CONFIDENTIAL'

    engine = create_engine(f'{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{HOST}/{DATABASE}')
    connection = engine.connect()
    metadata = MetaData()
    table = Table('your_table_name', metadata, autoload_with=engine)

    query = select([
        table.c.REF_CODE,
        table.c.PREFIX,
        table.c.BANK_PLACEMENT,
        table.c.CH_CODE,
        table.c.AGENT_TAGGING,
        table.c.AGENT,
        table.c.FINAL_AGENT,
        table.c.FINAL_SS,
        table.c.STATUS,
        table.c.NEGO_BUDDY,
        table.c.FINAL_SSS,
        table.c.NAME,
        table.c.ACCOUNTNUMBER,
        table.c.DATE,
        table.c.AMOUNT,
        table.c.CURRENCY,
        table.c.FINAL_AMOUNT,
        table.c.CUSTOMER_BLOCK_CODE,
        table.c.UNIT_CODE,
        table.c.PLACEMENT,
        table.c.FINAL_PLACEMENT,
        table.c.CF_RATE,
        table.c.CF_AMOUNT,
        table.c.TYPE_OF_PAYMENT,
        table.c.PAYMENT_SOURCE,
        table.c.CF_TIER
    ])

    result = connection.execute(query)
    rows = result.fetchall()
    connection.close()
    return pd.DataFrame(rows, columns=query.columns.keys())
