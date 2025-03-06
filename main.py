import streamlit as st 
import pandas as pd
import os 
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

# Set up our App
st.set_page_config(page_title="Data Sweeper Pro", layout='wide')
st.title("Data Sweeper Pro")
st.write("Transform your files between CSV and Excel formats with built-in AI-powered insights, data cleaning, and visualization!")

uploaded_files = st.file_uploader("Upload your files (CSV or Excel):", type=["csv", "xlsx"], accept_multiple_files=True)

def clean_text_columns(df):
    text_cols = df.select_dtypes(include=['object']).columns
    df[text_cols] = df[text_cols].apply(lambda x: x.str.strip().str.replace(r'[^a-zA-Z0-9 ]', '', regex=True).str.lower())
    return df

def convert_categorical_to_numeric(df):
    categorical_cols = df.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        df[col] = df[col].astype('category').cat.codes
    return df

if uploaded_files:
    processed_files = []
    merged_df = None

    for file in uploaded_files:
        file_ext = os.path.splitext(file.name)[-1].lower()

        if file_ext == ".csv":
            df = pd.read_csv(file)
        elif file_ext == ".xlsx":
            df = pd.read_excel(file)
        else:
            st.error(f"Unsupported file type: {file_ext}")
            continue        

        # Display info about the file 
        st.write(f"*File Name:* {file.name}")
        st.write(f"*File Size:* {file.size/1024:.2f} KB")

        # Show 5 rows of our df
        st.write("Preview the Head of the DataFrame")
        st.dataframe(df.head())

        # Data Summary Feature
        st.subheader("Data Summary")
        if st.checkbox(f"Show Summary for {file.name}"):
            st.write(df.describe(include='all'))

        # AI Insights
        st.subheader("AI-Powered Insights")
        if st.checkbox(f"Show AI Insights for {file.name}"):
            numeric_df = df.select_dtypes(include=['number'])
            if numeric_df.empty:
                df = convert_categorical_to_numeric(df)
                numeric_df = df.select_dtypes(include=['number'])
            
            if not numeric_df.empty:
                correlation_matrix = numeric_df.corr()
                st.write("Feature Correlations:")
                fig, ax = plt.subplots(figsize=(8, 6))
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', ax=ax)
                st.pyplot(fig)
            else:
                st.write("No numerical columns available for correlation analysis even after conversion.")

        # Data Cleaning Options
        st.subheader("Data Cleaning Options")
        if st.checkbox(f"Clean Data for {file.name}"):
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"Remove Duplicates from {file.name}"):
                    df.drop_duplicates(inplace=True)
                    st.write("Duplicates Removed!")

            with col2:
                if st.button(f"Fill Missing Values for {file.name}"):
                    df.fillna(df.mode().iloc[0], inplace=True)
                    st.write("Missing Values have been Filled!")
            
            with col3:
                if st.button(f"Standardize Text Columns for {file.name}"):
                    df = clean_text_columns(df)
                    st.write("Text Columns Standardized!")

        # Choose Specific Columns to Keep or Convert
        st.subheader("Select Columns to Convert")
        columns = st.multiselect(f"Choose Columns for {file.name}", df.columns, default=df.columns)
        df = df[columns]  

        # Create Advanced Visualizations
        st.subheader("Data Visualization")  
        if st.checkbox(f"Show Visualization for {file.name}"):
            col1, col2 = st.columns(2)
            with col1:
                st.bar_chart(df.select_dtypes(include='number').iloc[:, :2])
            with col2:
                fig, ax = plt.subplots()
                df[df.columns[0]].value_counts().plot.pie(autopct="%1.1f%%", ax=ax)
                st.pyplot(fig)

        # Convert the File -> CSV to Excel
        st.subheader("Conversion Options")
        conversion_type = st.radio(f"Convert {file.name} to:", ["CSV", "Excel"], key=file.name)
        if st.button(f"Convert {file.name}"):
            buffer = BytesIO()
            if conversion_type == "CSV":
                df.to_csv(buffer, index=False)
                file_name = file.name.replace(file_ext, ".csv")
                mime_type = "text/csv"
            elif conversion_type == "Excel":
                df.to_excel(buffer, index=False)
                file_name = file.name.replace(file_ext, ".xlsx")
                mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            buffer.seek(0)  

            # Download Button
            st.download_button(
                label=f"Download {file.name} as {conversion_type}",
                data=buffer,
                file_name=file_name,
                mime=mime_type
            )
        
        if merged_df is None:
            merged_df = df
        else:
            merge_col = st.selectbox(f"Select Merge Column for {file.name}", df.columns, key=f"merge_{file.name}")
            merged_df = pd.merge(merged_df, df, on=merge_col, how='outer')

        processed_files.append(file.name)

    if len(uploaded_files) > 1:
        st.subheader("Download Merged File")
        if st.button("Download Merged Data"):
            buffer = BytesIO()
            merged_df.to_csv(buffer, index=False)
            buffer.seek(0)
            st.download_button("Download Merged CSV", data=buffer, file_name="merged_data.csv", mime="text/csv")

    st.success(f"All files processed successfully: {', '.join(processed_files)}")
