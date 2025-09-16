import streamlit as st
import requests
import time

# Set the title of the app
st.title("Advanced AI-Powered Document Management System")

# Sidebar for app settings or user instructions
st.sidebar.title("Options")
st.sidebar.write("Upload documents and manage versions, or summarize documents.")

# Multiple file uploader widget to upload documents
uploaded_files = st.file_uploader("Upload your documents", type=["pdf", "docx", "pptx", "csv", "xlsx"], accept_multiple_files=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        st.write(f"File uploaded: {uploaded_file.name} ({uploaded_file.size/1024:.2f} KB)")

        # Display file metadata
        file_metadata = {
            "Filename": uploaded_file.name,
            "File Type": uploaded_file.type,
            "File Size": f"{uploaded_file.size / 1024:.2f} KB"
        }
        st.json(file_metadata)

        # Progress bar for file upload and processing
        progress_bar = st.progress(0)
        with st.spinner(f"Processing {uploaded_file.name}..."):
            files = {"file": uploaded_file.getvalue()}
            try:
                response = requests.post("http://localhost:8000/upload/", files={"file": uploaded_file})
                if response.status_code == 200:
                    st.success(f"File {uploaded_file.name} uploaded successfully!")
                else:
                    st.error(f"Failed to upload {uploaded_file.name}.")
            except Exception as e:
                st.error(f"An error occurred: {e}")
            
            # Simulate progress bar filling
            for i in range(100):
                time.sleep(0.02)
                progress_bar.progress(i + 1)

# Query document by Document ID
st.subheader("Query Document Archive")
document_id = st.text_input("Enter Document ID to view details or version history")

if document_id:
    response = requests.get(f"http://localhost:8000/document/{document_id}")
    if response.status_code == 200:
        st.json(response.json())
    else:
        st.error(f"Document with ID {document_id} not found.")

# Summarize document
st.subheader("Summarize Document")
if document_id:
    if st.button("Summarize Document"):
        response = requests.post(f"http://localhost:8000/document/{document_id}/summarize/")
        if response.status_code == 200:
            summary = response.json().get("summary", "No summary available.")
            st.write(summary)
        else:
            st.error("Error summarizing the document.")

# Footer section with additional instructions or help
st.sidebar.write("Need help? Contact the admin or refer to the documentation.")
