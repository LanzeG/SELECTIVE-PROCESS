# querydb.py

import pymysql
import pandas as pd

def get_database_connection():
    return pymysql.connect(
        host='192.168.15.197',
        user='ljbernas_bcp',
        password='$C4Ov9P52n1sh',
        database='bcrm',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def query_database(mapped_data):
    connection = get_database_connection()
    try:
        with connection.cursor() as cursor:
            base_query = """
            SELECT
                `client`.`client_name` AS 'campaign',
                `leads_result`.`leads_result_id` AS 'ResultID',
                `users`.`users_username` AS 'Agent',
                `leads`.`leads_chcode` AS 'chCode',
                `leads`.`leads_chname` AS 'chName',
                `leads`.`leads_placement` AS 'placement',
                `leads`.`leads_acctno` AS 'AccountNumber',
                `leads_status`.`leads_status_name` AS 'Status',
                `leads_result`.`leads_result_amount` AS 'Amount',
                `leads_result`.`leads_result_ts` AS 'ResultDate',
                `leads_result`.`leads_result_source` AS 'source',
                `leads`.`leads_endo_date` AS 'EndoDate',
                `leads`.`leads_ob` AS 'OB',
                leads_result.`leads_result_barcode_date`
            FROM `bcrm`.`leads_result`
            LEFT JOIN `bcrm`.`leads` ON (`leads_result`.`leads_result_lead` = `leads`.`leads_id`)
            LEFT JOIN `bcrm`.`client` ON (`leads`.`leads_client_id` = `client`.`client_id`)
            LEFT JOIN `bcrm`.`users` ON (`leads_result`.`leads_result_users` = `users`.`users_id`)
            LEFT JOIN `bcrm`.`users` AS leads_users ON (leads_users.`users_id` = leads.`leads_users_id`)
            LEFT JOIN `bcrm`.`leads_status` ON (`leads_result`.`leads_result_status_id` = `leads_status`.`leads_status_id`)
            LEFT JOIN `bcrm`.`leads_substatus` ON (`leads_result`.`leads_result_substatus_id` = `leads_substatus`.`leads_substatus_id`)
            WHERE `leads_users`.`users_username` <> 'POUT'
            """
            
            conditions = []
            values = []
            for col, db_col in mapped_data.items():
                if db_col and pd.notna(col):
                    conditions.append(f"`leads`.`{db_col}` = %s")
                    values.append(col)
            
            if conditions:
                query = base_query + " AND " + " AND ".join(conditions)
            else:
                query = base_query

            cursor.execute(query, values)
            result = cursor.fetchall()
            
            return result
    finally:
        connection.close()

def process_uploaded_file(df, header_mapping):
    valid_data = []
    invalid_data = []

    for index, row in df.iterrows():
        mapped_data = {header_mapping[col]: row[col] for col in df.columns if col in header_mapping and header_mapping[col]}

        # Prioritize account number and date for the query
        account_number = mapped_data.get('AccountNumber')
        date = mapped_data.get('ResultDate')

        if pd.isna(account_number) or pd.isna(date):
            # If either account number or date is missing, fall back to other fields
            result = query_database(mapped_data)
        else:
            date_str = pd.to_datetime(date).strftime('%Y-%m-%d')
            result = query_database({**mapped_data, 'AccountNumber': account_number, 'ResultDate': date_str})

        if result:
            valid_data.append(row)
        else:
            invalid_data.append(row)

    valid_df = pd.DataFrame(valid_data)
    invalid_df = pd.DataFrame(invalid_data)

    return valid_df, invalid_df
