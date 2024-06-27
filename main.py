import streamlit as st
import pandas as pd
from io import BytesIO

# Predefined template headers
template_headers = ["Customer Name", "Customer ID", "Amount", "Placement", "Date"]

def main():
    st.title("Excel Header Mapping and Value Extraction")

    # Step 1: Upload the Excel file
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

    if uploaded_file is not None:
        # Step 2: Read the uploaded Excel file
        with st.status("Merging excels...", expanded=True) as status:
            df = pd.read_excel(uploaded_file)
            st.write("Uploaded Excel file preview:")
            st.dataframe(df.head())

            # Step 3: Map the headers
            st.write("Map the headers:")
            mapping = {}

            # Convert both uploaded headers and template headers to uppercase for comparison
            uploaded_headers_upper = {header.upper(): header for header in df.columns}
            template_headers_upper = [header.upper() for header in template_headers]

            for template_header in template_headers:
                template_header_upper = template_header.upper()
                if template_header_upper in uploaded_headers_upper:
                    original_header = uploaded_headers_upper[template_header_upper]
                    mapping[template_header] = original_header
                else:
                    mapping[template_header] = None

            st.write("Header Mapping:", mapping)

            # Step 4: Extract values based on mapped headers
            extracted_data = {}
            for template_header, original_header in mapping.items():
                if original_header is not None:
                    # Convert all values to strings
                    extracted_data[template_header] = df[original_header].astype(str)
                else:
                    extracted_data[template_header] = [""] * len(df)

            mapped_df = pd.DataFrame(extracted_data)

            st.write("Mapped DataFrame preview:")
            st.dataframe(mapped_df.head())

            # Step 5: Write extracted values into a templated Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                mapped_df.to_excel(writer, index=False, sheet_name='Sheet1')
            output.seek(0)

            # Step 6: Provide download link for the templated Excel file
            st.download_button(
                label="Download Mapped Excel",
                data=output,
                file_name="mapped_excel.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            status.update(label=f"Merging completed! ", state="complete", expanded=False)

if __name__ == "__main__":
    main()
