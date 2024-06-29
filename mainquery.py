import streamlit as st
import pandas as pd
from io import BytesIO
import datetime
import os
from openpyxl.utils import get_column_letter
from openpyxl import Workbook
from querydb import query_database

def load_template_headers():
    try:
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

template_headers = load_template_headers()
if template_headers is None:
    st.stop()

def load_header_mappings():
    try:
        mappings_df = pd.read_excel('header_mappings.xlsx')
        
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

def process_each_sheet(uploaded_file):
    try:
        xls = pd.ExcelFile(uploaded_file)
        dfs = []

        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)
            dfs.append(df)

        return dfs
    except Exception as e:
        st.error(f"Error processing Excel sheets: {e}")
        return None

def fill_missing_headers(df, template_headers):
    for header in template_headers:
        if header not in df.columns:
            df[header] = None
    return df

def compare_dataframes(final_df, template_df):
    mismatched_rows = []
    for index, row in final_df.iterrows():
        if not row.equals(template_df.loc[index]):
            mismatched_rows.append(index)
    return mismatched_rows

def main():
    st.title("Automation Selective tool")
    st.markdown("""
    ### Instructions:
    1. Consider removing the design of Raw file if the first (1) COL and ROW is not HEADER
    2. Before the automation please FEED the possible headers to make it accurate
    3. Upload CSV/XLSX file
    4. Download the OUTPUT file.
    5. Expect it may be slow due to QUERY from BCRM.

    (Note: It does not accept xls file, consider resave the file as csv or xlsx)
    """)

    uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "csv"])

    if uploaded_file is not None:
        original_file_name = os.path.splitext(uploaded_file.name)[0]

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

            for df in dfs:
                df.columns = df.columns.map(str)

            st.write("Uploaded file preview:")
            st.dataframe(dfs[0].head())

            header_mappings = load_header_mappings()
            if header_mappings is None:
                return

            final_df = pd.DataFrame(columns=template_headers)

            for df in dfs:
                mapping = map_headers(df, header_mappings)

                valid_headers = [header for header in mapping.values() if header is not None]
                if len(valid_headers) < 2:
                    st.write(f"Skipping sheet as it does not contain at least two template headers.")
                    continue

                st.write("Header Mapping:", mapping)

                extracted_data = {}
                for template_header, original_header in mapping.items():
                    if original_header is not None:
                        extracted_data[template_header] = df[original_header].copy()
                    else:
                        extracted_data[template_header] = pd.Series([None] * len(df))

                mapped_df = pd.DataFrame(extracted_data)
                final_df = pd.concat([final_df, mapped_df], ignore_index=True)

            st.write("OUTPUT PREVIEW:")
            st.dataframe(final_df.head())

            # Fill missing headers
            final_df = fill_missing_headers(final_df, template_headers)

            # Query the database
            template_df = query_database()

            # Compare DataFrames
            mismatched_rows = compare_dataframes(final_df, template_df)
            if mismatched_rows:
                st.write(f"Mismatched rows: {mismatched_rows}")
            else:
                st.write("All rows match the expected template.")

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                final_df.to_excel(writer, index=False, sheet_name='Sheet1')

                worksheet = writer.sheets['Sheet1']
                for col in worksheet.columns:
                    max_length = 0
                    column_letter = col[0].column_letter
                    for cell in col:
                        try:
                            if isinstance(cell.value, (int, float)):
                                cell_value_str = f"{cell.value:.0f}"
                            else:
                                cell_value_str = str(cell.value)
                            
                            if len(cell_value_str) > max_length:
                                max_length = len(cell_value_str)
                        except:
                            pass
                    adjusted_width = (max_length + 2) * 1.2
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            output.seek(0)

            current_date = datetime.datetime.now().strftime("%Y%m%d")

            st.download_button(
                label="Download Output",
                data=output,
                file_name=f"{original_file_name}_processed_{current_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

if __name__ == "__main__":
    main()
