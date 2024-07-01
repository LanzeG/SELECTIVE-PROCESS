import streamlit as st
import pandas as pd
import openpyxl
import io
import msoffcrypto

def unlock_excel(file_content, password):
    try:
        # Use msoffcrypto to handle the password protection
        decrypted = io.BytesIO()
        office_file = msoffcrypto.OfficeFile(file_content)
        office_file.load_key(password=password)
        office_file.decrypt(decrypted)

        # Load the decrypted file into openpyxl
        decrypted.seek(0)
        workbook = openpyxl.load_workbook(decrypted, read_only=False, data_only=True, keep_vba=False, keep_links=False)

        # Save the unlocked workbook to a BytesIO object
        unlocked_file = io.BytesIO()
        workbook.save(unlocked_file)
        unlocked_file.seek(0)
        return unlocked_file
    except Exception as e:
        raise Exception(f"Error unlocking the file: {str(e)}")

def main():
    st.title("Unlock Excel File")
    st.write("Upload an Excel file and enter the password if it's protected:")

    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
    password = st.text_input("Password", type="password")

    if uploaded_file and password:
        try:
            # Read the uploaded file into a BytesIO object
            file_content = io.BytesIO(uploaded_file.getvalue())
            unlocked_file = unlock_excel(file_content, password)
            st.success("File unlocked successfully!")
            st.download_button("Download Unlocked File", unlocked_file, file_name="unlocked_file.xlsx")
        except Exception as e:
            st.error(str(e))

if __name__ == "__main__":
    main()
