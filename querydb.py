# from sqlalchemy import create_engine, MetaData, Table, select, and_, or_
# import pandas as pd

# def query_database():
#     engine = create_engine(
#         'mysql+pymysql://{user}:{pw}@{host}/{db}'.format(
#             user="ljbernas_bcp",
#             pw="$C4Ov9P52n1sh",
#             host="192.168.15.197",
#             db="bcrm"
#         )
#     )

#     connection = engine.connect()
#     metadata = MetaData()
#     leads_result = Table('leads_result', metadata, autoload_with=engine)
#     leads = Table('leads', metadata, autoload_with=engine)
#     client = Table('client', metadata, autoload_with=engine)
#     users = Table('users', metadata, autoload_with=engine)
#     leads_status = Table('leads_status', metadata, autoload_with=engine)
#     leads_substatus = Table('leads_substatus', metadata, autoload_with=engine)
#     leads_users = users.alias('leads_users')

#     query = select(
#         client.c.client_name.label('campaign'),
#         leads_result.c.leads_result_id.label('ResultID'),
#         users.c.users_username.label('Agent'),
#         leads.c.leads_chcode.label('chCode'),
#         leads.c.leads_chname.label('chName'),
#         leads.c.leads_placement.label('placement'),
#         leads.c.leads_acctno.label('AccountNumber'),
#         leads_status.c.leads_status_name.label('Status'),
#         leads_substatus.c.leads_substatus_name.label('subStatus'),
#         leads_result.c.leads_result_amount.label('Amount'),
#         leads_result.c.leads_result_sdate.label('StartDate'),
#         leads_result.c.leads_result_edate.label('EndDate'),
#         leads_result.c.leads_result_ornumber.label('ORNumber'),
#         leads_result.c.leads_result_comment.label('Notes'),
#         leads.c.leads_new_address.label('NewAddress'),
#         leads.c.leads_new_contact.label('NewContact'),
#         leads_result.c.leads_result_ts.label('ResultDate'),
#         leads_result.c.leads_result_source.label('source'),
#         leads.c.leads_endo_date.label('EndoDate'),
#         leads.c.leads_ob.label('OB'),
#         leads_result.c.leads_result_barcode_date
#     ).select_from(
#         leads_result
#         .outerjoin(leads, leads_result.c.leads_result_lead == leads.c.leads_id)
#         .outerjoin(client, leads.c.leads_client_id == client.c.client_id)
#         .outerjoin(users, leads_result.c.leads_result_users == users.c.users_id)
#         .outerjoin(leads_users, leads_users.c.users_id == leads.c.leads_users_id)
#         .outerjoin(leads_status, leads_result.c.leads_result_status_id == leads_status.c.leads_status_id)
#         .outerjoin(leads_substatus, leads_result.c.leads_result_substatus_id == leads_substatus.c.leads_substatus_id)
#     ).where(
#         leads_users.c.users_username != 'POUT'
#     )

#     result = connection.execute(query)
#     rows = result.fetchall()
#     connection.close()
#     return pd.DataFrame(rows, columns=query.columns.keys())

# # Execute the function and get the data as a DataFrame
# df = query_database()
# print(df)
import streamlit as st
from sqlalchemy import create_engine, MetaData, Table, select, and_, or_
import pandas as pd

def query_database():
    engine = create_engine(
        'mysql+pymysql://{user}:{pw}@{host}/{db}'.format(
            user="ljbernas_bcp",
            pw="$C4Ov9P52n1sh",
            host="192.168.15.197",
            db="bcrm"
        )
    )

    connection = engine.connect()
    metadata = MetaData()
    leads_result = Table('leads_result', metadata, autoload_with=engine)
    leads = Table('leads', metadata, autoload_with=engine)
    client = Table('client', metadata, autoload_with=engine)
    users = Table('users', metadata, autoload_with=engine)
    leads_status = Table('leads_status', metadata, autoload_with=engine)
    leads_substatus = Table('leads_substatus', metadata, autoload_with=engine)
    leads_users = users.alias('leads_users')

    query = select(
        client.c.client_name.label('campaign'),
        leads_result.c.leads_result_id.label('ResultID'),
        users.c.users_username.label('Agent'),
        leads.c.leads_chcode.label('chCode'),
        leads.c.leads_chname.label('chName'),
        leads.c.leads_placement.label('placement'),
        leads.c.leads_acctno.label('AccountNumber'),
        leads_status.c.leads_status_name.label('Status'),
        leads_substatus.c.leads_substatus_name.label('subStatus'),
        leads_result.c.leads_result_amount.label('Amount'),
        leads_result.c.leads_result_sdate.label('StartDate'),
        leads_result.c.leads_result_edate.label('EndDate'),
        leads_result.c.leads_result_ornumber.label('ORNumber'),
        # leads_result.c.leads_result_comment.label('Notes'),
        # leads.c.leads_new_address.label('NewAddress'),
        # leads.c.leads_new_contact.label('NewContact'),
        leads_result.c.leads_result_ts.label('ResultDate'),
        leads_result.c.leads_result_source.label('source'),
        leads.c.leads_endo_date.label('EndoDate'),
        leads.c.leads_ob.label('OB'),
        leads_result.c.leads_result_barcode_date
    ).select_from(
        leads_result
        .outerjoin(leads, leads_result.c.leads_result_lead == leads.c.leads_id)
        .outerjoin(client, leads.c.leads_client_id == client.c.client_id)
        .outerjoin(users, leads_result.c.leads_result_users == users.c.users_id)
        .outerjoin(leads_users, leads_users.c.users_id == leads.c.leads_users_id)
        .outerjoin(leads_status, leads_result.c.leads_result_status_id == leads_status.c.leads_status_id)
        .outerjoin(leads_substatus, leads_result.c.leads_result_substatus_id == leads_substatus.c.leads_substatus_id)
    ).where(
        leads_users.c.users_username != 'POUT'
    ).limit(50)

    result = connection.execute(query)
    rows = result.fetchall()
    connection.close()
    return pd.DataFrame(rows, columns=query.columns.keys())

# Execute the function and get the data as a DataFrame
df = query_database()

# Display the dataframe using st.dataframe
st.dataframe(df)
