import streamlit as st
import pandas as pd
from openpyxl import load_workbook
import io
import msoffcrypto 
import pandas as pd
import io
from querydb import query_database

def unlock_excel(file_content, password):
    try:
        # Use msoffcrypto to handle the password protection
        decrypted = io.BytesIO()
        office_file = msoffcrypto.OfficeFile(file_content)
        office_file.load_key(password=password)
        office_file.decrypt(decrypted)

        # Load the decrypted file into openpyxl
        decrypted.seek(0)
        workbook = load_workbook(decrypted, read_only=False, data_only=True, keep_vba=False, keep_links=False)

        # Save the unlocked workbook to a BytesIO object
        unlocked_file = io.BytesIO()
        workbook.save(unlocked_file)
        unlocked_file.seek(0)
        return unlocked_file
    except Exception as e:
        raise Exception(f"{str(e)}")

def load_template_headers():
    try:
        # Load the template headers from the "Template Header" column of the external Excel file
        mappings_df = pd.read_excel('header_mappings.xlsx')
        if 'Template Header' not in mappings_df.columns:
            st.error("The header_mappings.xlsx file must contain 'Template Header' column.")
            return None
        
        template_headers = mappings_df['Template Header'].dropna().unique().tolist()
        template_headers = [header.strip().upper() for header in template_headers]
        return template_headers
    except Exception as e:
        st.error(f"Error loading template headers: {e}")
        return None
    
# Load template headers from the Excel file
template_headers = load_template_headers()
if template_headers is None:
    st.stop()
    
def load_header_mappings():
    try:
        # Load the header mappings from an external Excel file
        mappings_df = pd.read_excel('header_mappings.xlsx')
        
        # Verify that the required columns exist
        if 'Template Header' not in mappings_df.columns or 'Possible Headers' not in mappings_df.columns:
            st.error("The header_mappings.xlsx file must contain 'Template Header' and 'Possible Headers' columns.")
            return None
        
        header_mappings = {}
        for _, row in mappings_df.iterrows():
            template_header = str(row['Template Header']).strip().upper() if not pd.isna(row['Template Header']) else ''
            possible_headers = str(row['Possible Headers']).strip().upper().split(', ') if not pd.isna(row['Possible Headers']) else []
            if template_header not in header_mappings:
                header_mappings[template_header] = []
            header_mappings[template_header].extend(possible_headers)
        return header_mappings
    
    except Exception as e:
        st.error(f"Error loading header mappings: {e}")
        return None
    
    

def map_headers(df, header_mappings):
    if header_mappings is None:
        return {}
    
    mapping = {}
    uploaded_headers_upper = {header.upper().strip(): header for header in df.columns}
    for template_header in template_headers:
        template_header_upper = template_header.upper()
        possible_headers = header_mappings.get(template_header_upper, [])
        mapped_header = None
        for possible_header in possible_headers:
            if possible_header in uploaded_headers_upper:
                mapped_header = uploaded_headers_upper[possible_header]
                break
        mapping[template_header] = mapped_header
   
    return mapping
    
def add_ch_code_prefix(df):
    # Check for 'CH CODE' column (case-insensitive)
    ch_code_col = next((col for col in df.columns if col.strip().upper() == 'CH CODE'), None)
    
    if ch_code_col is None:
        print("CH CODE column not found in the uploaded file.")
        return df

    # Ensure 'PREFIX' column exists, initialize with None if it doesn't
    if 'PREFIX' not in df.columns:
        df['PREFIX'] = None

    # Process each row to update 'PREFIX' column
    for index, row in df.iterrows():
        ch_code = row[ch_code_col]
        if pd.notnull(ch_code) and isinstance(ch_code, str):
            # Remove hyphens and take the first 6 characters
            cleaned_code = ch_code.replace('-', '')
            prefix = cleaned_code[:6]  # Extract first 6 characters as prefix
            df.at[index, 'PREFIX'] = prefix  # Update the 'PREFIX' column in the DataFrame
        else:
            df.at[index, 'PREFIX'] = None  # Handle NaN or NaT values

    return df


def process_each_sheet(uploaded_file):
    try:
        # Load the uploaded Excel file
        xls = pd.ExcelFile(uploaded_file)
        dfs = []
        sheet_names = []

        for sheet_name in xls.sheet_names:
            # Read each sheet into a DataFrame
            df = pd.read_excel(xls, sheet_name=sheet_name)
            dfs.append(df)
            sheet_names.append(sheet_name)

        return dfs, sheet_names
    except Exception as e:
        st.error(f"Error processing Excel sheets: {e}")
        return None, None

def prevent_scientific_notation(df):
    if 'ACCOUNTNUMBER' in df.columns:
        df['ACCOUNTNUMBER'] = df['ACCOUNTNUMBER'].apply(lambda x: f"{int(x):d}" if pd.notna(x) else None)
        df['ACCOUNTNUMBER'] = df['ACCOUNTNUMBER'].astype(str)
    return df

def fill_missing_fields(final_df, template_headers):
    # Read the Excel file containing column mappings
    mapping_df = pd.read_excel('column_mapping.xlsx')

    # Convert the mapping DataFrame to a dictionary
    column_mapping = mapping_df.set_index('SQL Column Name')['DataFrame Column Header'].to_dict()

    for index, row in final_df.iterrows():
        # Extract account number and date from the current row
        account_number = row['ACCOUNTNUMBER']
        query_date = row['DATE']  # Assuming 'DATE' column exists in final_df
        client_name = row['CAMPAIGN']
        
        if pd.notna(account_number) and pd.notna(query_date) and pd.notna(client_name):
            # Query database for the row's account number and date
            try:
                result = query_database(client_name, account_number, query_date)
                if result:
                    # Print the type of result for debugging purposes
                    print(type(result))
                    print(result)
                    
                    # Update missing fields in final_df with database query result
                    for key, value in result.items():
                        if key in column_mapping:
                            final_df.loc[index, column_mapping[key]] = value
            except Exception as e:
                st.error(f"Error querying database for row {index}: {e}")

    return final_df