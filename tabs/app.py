import streamlit as st
import pandas as pd
import os

def run():
    # Define the template headers
    template_headers = [
        "REF CODE", "BANK/PLACEMENT", "Ch code", "AGENT", "TAGGING AGENT", "Final Agent",
        "Final SS", "STATUS", "NEGO BUDDY", "Final SSS", "NAME", "ACCOUNTNUMBER", "DATE",
        "AMOUNT", "CURRENCY", "FINAL AMOUNT", "Customer Block Code", "UNIT CODE",
        "PLACEMENT", "FINAL PLACEMENT", "CF RATE", "CF AMOUNT", "TYPE OF PAYMENT", "PAYMENT SOURCE"
    ]

    # Sort the template headers alphabetically
    template_headers.sort()

    # Path to the existing Excel file
    file_path = "header_mappings.xlsx"

    # Check if the file exists, create it if it doesn't
    if not os.path.exists(file_path):
        initial_df = pd.DataFrame(columns=["Template Header", "Possible Headers"])
        initial_df.to_excel(file_path, index=False)

    # Load the existing mappings
    existing_df = pd.read_excel(file_path)

    # Create a dictionary to hold the mappings
    header_mappings = {header: "" for header in template_headers}

    st.title("Input possible headers")

    # Create input fields for each template header
    for header in template_headers:
        header_mappings[header] = st.text_input(f"Possible header for {header}", key=header)

    # Button to update the Excel file
    if st.button("Update Excel File"):
        # Filter out empty values and create a DataFrame for new mappings
        new_mappings = [(k, v) for k, v in header_mappings.items() if v]
        new_mappings_df = pd.DataFrame(new_mappings, columns=["Template Header", "Possible Headers"])
        
        # Append the new mappings to the existing DataFrame
        updated_df = pd.concat([existing_df, new_mappings_df], ignore_index=True)
        
        # Sort the DataFrame by "Template Header"
        updated_df = updated_df.sort_values(by="Template Header").reset_index(drop=True)
        
        # Save the updated DataFrame back to the Excel file
        updated_df.to_excel(file_path, index=False)
        
        st.success("Excel file has been updated successfully!")
