import pymysql
from time import sleep

def query_database(client_name, account_number, ch_code, customer_name, customer_id):
    try:
        # Establish connection to your database
        connection = pymysql.connect(host='192.168.15.197',
                                     user='ljbernas',
                                     password='$C4Ov9P52n1sh',
                                     database='bcrm',
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        dynamic_query = ["leads_users.users_username <> 'POUT' "]
        if client_name: 
            dynamic_query.append(f"`client`.`client_name` = '{client_name}'")
        if account_number:
            dynamic_query.append(f"`leads`.`leads_acctno` LIKE '%{account_number}'")
        elif customer_name:
            dynamic_query.append(f"`leads`.`leads_acctno` LIKE '%{customer_id}'")
        if ch_code:
            dynamic_query.append(f"`leads`.`leads_chcode` = '{ch_code}'")
        if customer_id:
            dynamic_query.append(f"`leads`.`leads_chname` = '{customer_name}'")

        # dynamic_query.append('`leads_status`.`leads_status_name` IN ("PTP", "CONFIRMS", "PTP EPA")')
        sql = f"""
        SELECT
            `client`.`client_name` AS 'campaign',
            `leads_result`.`leads_result_id` AS 'ResultID',
            `users`.`users_username` AS 'Agent',
            `leads`.`leads_chcode` AS 'chCode',
            `leads`.`leads_chname` AS 'chName',
            `leads`.`leads_placement` AS 'placement',
            `leads`.`leads_acctno` AS 'AccountNumber',
            `leads`.`leads_cycle` AS 'lev',
            `leads_status`.`leads_status_name` AS 'Status',
            `leads_result`.`leads_result_amount` AS 'Amount',
            `leads_result`.`leads_result_ts` AS 'ResultDate',
            `leads_result`.`leads_result_source`AS 'source',
            `leads`.`leads_endo_date` AS 'EndoDate',
            `leads`.`leads_block_code` AS 'block',
            `leads`.`leads_ob` AS 'OB',
            leads_result.`leads_result_barcode_date`
        FROM `bcrm`.`leads_result`
        LEFT JOIN `bcrm`.`leads` ON (`leads_result`.`leads_result_lead` = `leads`.`leads_id`)
        LEFT JOIN `bcrm`.`client` ON (`leads`.`leads_client_id` = `client`.`client_id`)
        LEFT JOIN `bcrm`.`users` ON (`leads_result`.`leads_result_users` = `users`.`users_id`)
        LEFT JOIN `bcrm`.`users` AS leads_users ON (leads_users.`users_id` = leads.`leads_users_id`)
        LEFT JOIN `bcrm`.`leads_status` ON (`leads_result`.`leads_result_status_id` = `leads_status`.`leads_status_id`)
        LEFT JOIN `bcrm`.`leads_substatus` ON (`leads_result`.`leads_result_substatus_id` = `leads_substatus`.`leads_substatus_id`) 
        LEFT JOIN `dynamic_value` AS dv8 ON (dv8.`dynamic_value_dynamic_id`=`leads_result`.`leads_result_lead`)
         WHERE
        """
        sql = sql +  ' AND '.join(dynamic_query)
        print(sql )

        # Execute SQL query with parameters
        with connection.cursor() as cursor:
            cursor.execute(sql)
            results = cursor.fetchall()
            
        return results[0] if results else None
        
    except Exception as e:
        print(f"Error querying database: {e}")
        sleep(5)
        # query_database(client_name, account_number, ch_code, customer_name, customer_id)
        return None
    finally:
        if connection:
            connection.close()
