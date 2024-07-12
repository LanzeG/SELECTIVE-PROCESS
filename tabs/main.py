import streamlit as st
import pandas as pd
from io import BytesIO
import datetime
import os
from openpyxl import load_workbook
import io
from functions import (
    load_header_mappings, 
    load_template_headers, 
    process_each_sheet, 
    prevent_scientific_notation, 
    add_ch_code_prefix, 
    unlock_excel, 
    map_headers, 
    fill_missing_fields
)
from querydb import query_database  # Assuming you saved the query function in query_function.py

def main():
    # Load template headers from the Excel file
    template_headers = load_template_headers()
    
    if template_headers is None:
        st.stop()

    st.title("Automation Selective tool")
    st.markdown("""
    ### Instructions:            
    1. Consider removing the design of Raw file if the first (1) COL and ROW is not HEADER
    2. Before the automation please FEED the possible headers to make it accurate
    3. Upload CSV/XLSX file
    4. Input the CSV/XLSX password if the system detects it as encrypted.
    5. Download the OUTPUT file.
    6. Expect it may be slow due to QUERY from BCRM.
    
    (Note: It does not accept xls file, consider resave the file as csv or xlsx)    
    """)

    # Step 1: Upload the file
    uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "csv"])

    if uploaded_file is not None:
        # Extract the original file name without extension
        original_file_name = os.path.splitext(uploaded_file.name)[0]
        
        # Step 2: Check if file is an Excel file and prompt for password if encrypted
        if uploaded_file.name.endswith('.xlsx'):
            file_content = io.BytesIO(uploaded_file.getvalue())
            try:
                # Try to load the workbook without a password
                workbook = load_workbook(file_content, read_only=False, data_only=True, keep_vba=False, keep_links=False)
                st.toast("File is not password protected, proceeding with automation! ✔️")
                dfs, sheet_names = process_each_sheet(uploaded_file)
            except Exception:
                password = st.text_input("Password", type="password")
                if password:
                    try:
                        unlocked_file = unlock_excel(file_content, password)
                        st.toast("File unlocked successfully! ✔️")
                        with st.spinner("Processing selectives..."):
                            try:
                                dfs, sheet_names = process_each_sheet(unlocked_file)
                                st.write("Excel sheets processed successfully.")
                            except Exception as e:
                                st.error(f"Failed to process the unlocked file: {e}")
                                st.stop()
                    except Exception as e:
                        st.error(str(e))
                        st.stop()
                else:
                    st.info("Please provide a password to unlock the file.")
                    st.stop()
        elif uploaded_file.name.endswith('.csv'):
            with st.spinner("Processing selectives..."):
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                    dfs = [df]
                    st.write("CSV file processed successfully.")
                except UnicodeDecodeError:
                    st.error(f"Failed to read the CSV file with 'utf-8' encoding. Trying 'latin1' encoding. {uploaded_file.name}")
                    try:
                        df = pd.read_csv(uploaded_file, encoding='latin1')
                        dfs = [df]
                        st.write("CSV file processed successfully with 'latin1' encoding.")
                    except UnicodeDecodeError:
                        st.error(f"Failed to read the CSV file with 'latin1' encoding. Trying 'iso-8859-1' encoding. {uploaded_file.name}")
                        try:
                            df = pd.read_csv(uploaded_file, encoding='iso-8859-1')
                            dfs = [df]
                            st.write("CSV file processed successfully with 'iso-8859-1' encoding.")
                        except UnicodeDecodeError:
                            st.error(f"Failed to read the CSV file with 'iso-8859-1' encoding. {uploaded_file.name}")
                            st.stop()
        
        else:
            st.info("Please upload a file.")
            st.stop()
            
        with st.status("Processing Selective...", expanded=False) as status:
            # Convert all column names to strings to avoid mixed-type warnings
            for df in dfs:
                df.columns = df.columns.map(str)
            
            st.write("Uploaded file preview:")
            st.dataframe(dfs[0].head())
            
            # Load header mappings from the database file
            header_mappings = load_header_mappings()
            if header_mappings is None:
                st.stop()

            # Prepare final DataFrame to hold appended data
            final_df = pd.DataFrame(columns=template_headers)
            
            for df, sheet_name in zip(dfs, sheet_names):
                
                # Step 5: Map the headers
                mapping = map_headers(df, header_mappings)
                
                # Check if the sheet contains at least two template headers
                valid_headers = [header for header in mapping.values() if header is not None]
                if len(valid_headers) < 2:
                    st.info(f"Skipping sheet ({sheet_name.upper()}) as it does not contain at least two template headers.")
                    continue
                st.write(sheet_name)
                st.json(mapping, expanded=False)

                # Step 6: Extract values based on mapped headers
                extracted_data = {}
                for template_header, original_header in mapping.items():
                    if original_header is not None:
                        extracted_data[template_header] = df[original_header].copy()
                    else:
                        extracted_data[template_header] = pd.Series([None] * len(df))

                mapped_df = pd.DataFrame(extracted_data)
                final_df = pd.concat([final_df, mapped_df], ignore_index=True)

                # Debug: Check the intermediate final_df
                st.write(f"Intermediate final_df after processing sheet {sheet_name}:")
                st.dataframe(final_df.head())
            
            # Step 7: Fill missing fields with None or default values
            final_df = fill_missing_fields(final_df, template_headers)
            
            # Debug: Check the final_df after filling missing fields
            st.write("final_df after filling missing fields:")
            st.dataframe(final_df.head())

            # Step 8: Add CH CODE Prefix to First Column if CH CODE exists
            final_df = prevent_scientific_notation(final_df)
            final_df = add_ch_code_prefix(final_df)

            # Prepare a DataFrame to hold the query results
            results_df = pd.DataFrame()

            # Query the database for each row and append results
            for _, row in final_df.iterrows():
                account_number = row.get('AccountNumber')
                client_name = row.get('campaign')
                ch_code = row.get('chCode')
                date = row.get('ResultDate')
                
                results = query_database(client_name, account_number, ch_code, date)
                if results:
                    # Append results to the results DataFrame
                    result_df = pd.DataFrame(results)
                    results_df = pd.concat([results_df, result_df], ignore_index=True)

            # Concatenate the original final_df with the results_df
            final_df = pd.concat([final_df, results_df], ignore_index=True)

            # Comparison logic for PAYMENT_DATE and RESULT_DATE
            if 'PAYMENT_DATE' in final_df.columns and 'RESULT_DATE' in final_df.columns:
                final_df['PAYMENT_DATE'] = pd.to_datetime(final_df['PAYMENT_DATE'], errors='coerce')
                final_df['RESULT_DATE'] = pd.to_datetime(final_df['RESULT_DATE'], errors='coerce')
                final_df['STATUS'] = final_df.apply(
                    lambda row: 'No Tag' if row['RESULT_DATE'] > row['PAYMENT_DATE'] else 'Ok on barcoded date',
                    axis=1
                )
                final_df['TAGGING AGENT'] = final_df.apply(
                    lambda row: 'MSPM' if row['STATUS'] == 'No Tag' else row['AGENT'],
                    axis=1
                )

            st.write("OUTPUT PREVIEW:")
            st.dataframe(final_df.head())

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Sheet1')

                # Auto-fit column widths
                worksheet = writer.sheets['Sheet1']
                for col in worksheet.columns:
                    max_length = 0
                    column_letter = col[0].column_letter  # Get the column letter
                    for cell in col:
                        try:  # Necessary to avoid error on empty cells
                            if isinstance(cell.value, (int, float)):
                                cell_value_str = f"{cell.value:.0f}"  # Format as integer without decimal places
                            else:
                                cell_value_str = str(cell.value)
                            
                            if len(cell_value_str) > max_length:
                                max_length = len(cell_value_str)
                        except:
                            pass
                    adjusted_width = (max_length + 2) * 1.2
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            output.seek(0)

            # Provide download link for the templated Excel file
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            new_file_name = f"{current_date}-{original_file_name}.xlsx"

            status.update(label=f"Process Complete!. {uploaded_file.name}", expanded=False)
        
        st.download_button(
            label="Download Mapped Excel",
            data=output,
            file_name=new_file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()
