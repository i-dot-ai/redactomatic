import streamlit as st
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
import json
import zipfile
from io import BytesIO
from unstructured.partition.auto import partition
import tempfile
from pathlib import Path
from uuid import uuid4

st.title("Redact-o-matic 🗑️")


INPUT_MODES = ["Text", "File Upload"]
input_mode = st.sidebar.radio("Select input mode", INPUT_MODES)

analyzer = AnalyzerEngine()
ENITITY_TYPES = analyzer.get_supported_entities()
default_entity_types = [
    "PERSON", 
    "PHONE_NUMBER", 
    "EMAIL_ADDRESS", 
    "AGE", 
    "ORGANIZATION", 
    "CREDIT_CARD", 
    "IP_ADDRESS", 
    "UK_NHS"
]

entities_to_extract = st.sidebar.multiselect(
    "Select PII types to redact", ENITITY_TYPES, default_entity_types
)

anonymizer = AnonymizerEngine()

def run_redaction(text, entities_to_extract):
    # Call analyzer to get results
    results = analyzer.analyze(text=text, entities=entities_to_extract, language="en")
    return results


if input_mode == "Text":
    default_text = "My name is Liam and my phone number is 212-555-5555"

    text = st.text_area("Enter text to redact", default_text)
    texts = {"raw_input": text}

elif input_mode == "File Upload":
    uploaded_files = st.file_uploader("Choose a file", accept_multiple_files=True)
    texts = {}

    for file_index, uploaded_file in enumerate(uploaded_files):
        bytes_data = uploaded_file.getvalue()
        file_path = Path(uploaded_file.name)

        # create a tempfile for the file
        temp_file = tempfile.NamedTemporaryFile(delete=True, suffix=file_path.suffix)
        temp_file.write(bytes_data)
        elements = partition(temp_file.name)
        text = ""
        for element in elements:
            text += element.text + "\n"
        texts[uploaded_file.name] = text

    
def anonymize_results(results):
    return anonymizer.anonymize(text=text, analyzer_results=results)


submit_button = st.button("Redact")

# Example output

def bold_redacted_items(text, items):
    for item in items:
        start = item["start"]
        end = item["end"]
        text = text[:start] + "**" + text[start:end] + "**" + text[end:]
    return text

if submit_button:
    text_results = {}

    progress_bar = st.progress(0)

    for i, file_name in enumerate(texts):
        text = texts[file_name]
        results = run_redaction(text, entities_to_extract)
        anonymized_text = anonymize_results(results)
        results = json.loads(anonymized_text.to_json())
        text_results[file_name] = results
        progress_bar.progress((i+1)/float(len(texts)))
    
    if len(texts.keys()) == 1:
        results = text_results[list(texts.keys())[0]]

        with st.expander("Preview Redacted Text"):
            st.markdown(bold_redacted_items(results["text"], results["items"]))

        st.download_button(
            label="Download redacted file", 
            data=results["text"], 
            file_name=f"{list(texts.keys())[0]}.txt", 
            mime="application/json"
        )
    else:
    # Create a zip file of the results

        zip_file = BytesIO()
        with zipfile.ZipFile(zip_file, "w") as zf:
            for file_name in text_results:
                results = text_results[file_name]
                zf.writestr(file_name+".txt", results["text"])
        
        st.download_button(
            label="Download redacted files", 
            data=zip_file.getvalue(), 
            file_name=f"redacted_files_{str(uuid4())}.zip", 
            mime="application/zip"
        )

