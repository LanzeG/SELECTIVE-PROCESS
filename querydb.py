import pymysql
import pandas as pd
from datetime import datetime

# Database connection parameters
DB_HOST = '192.168.15.197'
DB_USER = 'ljbernas_bcp'
DB_PASSWORD = '$C4Ov9P52n1sh'
DB_NAME = 'bcrm'
DB_CHARSET = 'utf8mb4'

def query_database(account_number, result_date):
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset=DB_CHARSET,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    query = """
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
        WHERE
            `leads_users`.`users_username` <> 'POUT' 
            AND `leads`.`leads_acctno` = %s
            AND DATE(`leads_result`.`leads_result_ts`) = %s;
    """
    
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (account_number, result_date))
            result = cursor.fetchone()
            return result

def validate_data(uploaded_df):
    valid_data = []
    invalid_data = []

    for index, row in uploaded_df.iterrows():
        account_number = row['ACCOUNT NUMBER']
        result_date = row['DATE']

        if pd.notna(account_number) and pd.notna(result_date):
            result_date_str = datetime.strptime(result_date, "%Y-%m-%d").strftime("%Y-%m-%d")
            db_record = query_database(account_number, result_date_str)

            if db_record:
                valid_data.append(row.to_dict())
            else:
                invalid_data.append(row.to_dict())
        else:
            invalid_data.append(row.to_dict())

    valid_df = pd.DataFrame(valid_data)
    invalid_df = pd.DataFrame(invalid_data)

    return valid_df, invalid_df

def add_autoid_and_prefix(df):
    if 'CH CODE' in df.columns:
        df['PREFIX'] = df['CH CODE'].apply(lambda x: x.replace('-', '')[:6] if pd.notna(x) else None)

    df['AUTOID'] = range(100000, 100000 + len(df))
    return df

def process_uploaded_file(uploaded_df):
    valid_df, invalid_df = validate_data(uploaded_df)

    valid_df = add_autoid_and_prefix(valid_df)
    invalid_df = add_autoid_and_prefix(invalid_df)

    return valid_df, invalid_df
