import streamlit as st
import pandas as pd

def load_template_headers():
    try:
        mappings_df = pd.read_excel('header_mappings.xlsx')
        if 'Template Header' not in mappings_df.columns:
            st.error("The header_mappings.xlsx file must contain 'Template Header' column.")
            return None
        template_headers = mappings_df['Template Header'].dropna().unique().tolist()
        return [header.strip().upper() for header in template_headers]
    except Exception as e:
        st.error(f"Error loading template headers: {e}")
        return None



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

template_headers = load_template_headers()
if template_headers is None:
    st.stop()
