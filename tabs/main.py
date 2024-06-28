import streamlit as st
import pandas as pd
from io import BytesIO
import datetime
import os
from openpyxl.utils import get_column_letter
from openpyxl import Workbook

# Predefined template headers
template_headers = [
    "Prefix",
    "REF CODE",
    "BANK/PLACEMENT",
    "Ch code",
    "AGENT",
    "TAGGING AGENT",
    "Final Agent",
    "Final SS",
    "STATUS",
    "NEGO BUDDY",
    "Final SSS",
    "NAME",
    "ACCOUNTNUMBER",
    "DATE",
    "AMOUNT",
    "CURRENCY",
    "FINAL AMOUNT",
    "Customer Block Code",
    "UNIT CODE",
    "PLACEMENT",
    "FINAL PLACEMENT",
    "CF RATE",
    "CF AMOUNT",
    "TYPE OF PAYMENT",
    "PAYMENT SOURCE"
]

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
            template_header = row['Template Header'].strip().upper()
            possible_header = row['Possible Headers'].strip().upper()
            if template_header not in header_mappings:
                header_mappings[template_header] = []
            header_mappings[template_header].append(possible_header)
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
    # for index, row in df.iterrows():
    #     if row['Ch code'] is not None:
    #         #row['Prefix'] = str(row['Ch code'])[:6]  # Extract first 6 characters as prefix
    #         df.loc[index, ["Prefix"]] == 
    #         print(str(row['Ch code'])[:6])
    # return df

    # df["Prefix"] = df["Ch code"].apply(lambda x: x[:6])
    # return df.copy()

    
    # if 'CH CODE' in df.columns:
    #     # Extract first 6 digits from 'CH CODE' column and store in 'Prefix'
    #     df['Prefix'] = df['CH CODE'].astype(str).str.extract(r'^(\d{6})')
    # else:
    #     # If 'CH CODE' column doesn't exist, create an empty 'Prefix' column
    #     df['Prefix'] = ''

    # # Reorder columns to ensure 'Prefix' is the first column
    # if 'Prefix' in df.columns:
    #     cols = ['Prefix'] + [col for col in df.columns if col != 'Prefix']
    #     df = df[cols]

    # return df

def process_each_sheet(uploaded_file):
    try:
        # Load the uploaded Excel file
        xls = pd.ExcelFile(uploaded_file)
        dfs = []

        for sheet_name in xls.sheet_names:
            # Read each sheet into a DataFrame
            df = pd.read_excel(xls, sheet_name=sheet_name)
            dfs.append(df)

        return dfs
    except Exception as e:
        st.error(f"Error processing Excel sheets: {e}")
        return None

def main():
    # Step 1: Upload the file
    uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "csv"])

    if uploaded_file is not None:
        # Extract the original file name without extension
        original_file_name = os.path.splitext(uploaded_file.name)[0]

        # Step 2: Read the uploaded file
        with st.status("Merging excels...", expanded=True) as status:
            try:
                if uploaded_file.name.endswith('.xlsx'):
                    dfs = process_each_sheet(uploaded_file)
                elif uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                    dfs = [df]
            except UnicodeDecodeError:
                status.update(label=f"Failed to read the CSV file with 'utf-8' encoding. Trying 'latin1' encoding. {uploaded_file.name}", state="error", expanded=True)
                try:
                    df = pd.read_csv(uploaded_file, encoding='latin1')
                    dfs = [df]
                except UnicodeDecodeError:
                    try:
                        status.update(label=f"Failed to read the CSV file with 'latin1' encoding. Trying 'iso-8859-1' encoding. {uploaded_file.name}", state="error", expanded=True)
                        df = pd.read_csv(uploaded_file, encoding='iso-8859-1')
                        dfs = [df]
                    except UnicodeDecodeError:
                        status.update(label=f"Failed to read the CSV file iso-8859-1 {uploaded_file.name}", state="error", expanded=False)
                        st.stop()

            # Convert all column names to strings to avoid mixed-type warnings
            for df in dfs:
                df.columns = df.columns.copy()
                
            st.write("Uploaded file preview:")
            st.dataframe(dfs[0].head())

            # Load header mappings from the database file
            header_mappings = load_header_mappings()
            if header_mappings is None:
                return

            # Prepare final DataFrame to hold appended data
            final_df = pd.DataFrame(columns=template_headers)

            for df in dfs:
                # Step 3: Add CH CODE Prefix to First Column if CH CODE exists
              

                # Step 5: Map the headers
                mapping = map_headers(df, header_mappings)
                
                # Check if the sheet contains at least two template headers
                valid_headers = [header for header in mapping.values() if header is not None]
                if len(valid_headers) < 2:
                    st.write(f"Skipping sheet as it does not contain at least two template headers.")
                    continue
                
                # st.write(f"Header Mapping for sheet:")
                st.write("Header Mapping:", mapping)

                # Step 6: Extract values based on mapped headers
                extracted_data = {}
                for template_header, original_header in mapping.items():
                    if original_header is not None:
                        extracted_data[template_header] = df[original_header].copy()
                    else:
                        extracted_data[template_header] = pd.Series([None] * len(df))

                mapped_df = pd.DataFrame(extracted_data)
                final_df = pd.concat([final_df, mapped_df], ignore_index=True)
            final_df = add_ch_code_prefix(final_df)
            st.write("OUTPUT PREVIEW:")
            st.dataframe(final_df.head())

            output = BytesIO()
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

            # Step 8: Provide download link for the templated Excel file
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            new_file_name = f"{current_date}-{original_file_name}.xlsx"

            status.update(label="Process Complete!", state="complete", expanded=False)

        st.download_button(
            label="Download Mapped Excel",
            data=output,
            file_name=new_file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
if __name__ == "__main__":
    main()
