
import os
import json
import streamlit as st


from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader


# Step 2: Load environment and configure Gemini LLM
google_api_key = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY"))

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=google_api_key
)

PROMPT_TEMPLATE = """
You are a resume parsing assistant. 
Return ONLY a valid JSON object (no markdown, no text).  

Schema:
{{
  "name": string | null,
  "email": string | null,
  "phone": string | null,
  "linkedin": string | null,
  "github": string | null,
  "location": string | null,
  "summary": string | null,
  "skills": [string],
  "experience": [
    {{
      "job_title": string | null,
      "company": string | null,
      "start_date": string | null,
      "end_date": string | "Present" | null,
      "currently_working": boolean,
      "description": string | null
    }}
  ],
  "education": [
    {{
      "degree": string | null,
      "institution": string | null,
      "year": string | null
    }}
  ],
  "projects": [
    {{
      "name": string | null,
      "description": string | null,
      "tech_stack": [string]
    }}
  ],
  "certifications": [string],
  "languages": [string],
  "parsing_confidence": number
}}

Now parse this resume and fill the fields accurately:
```{{resume_text}}```
Return ONLY the JSON — no explanations.
"""


# Proper initialization using from_template()
prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)


# Step 3: Helper function for loading resumes
def load_resume(uploaded_file):
    # Save uploaded file temporarily
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Choose loader based on file type
    if uploaded_file.name.endswith(".pdf"):
        loader = PyPDFLoader(temp_path)
    elif uploaded_file.name.endswith(".docx"):
        loader = Docx2txtLoader(temp_path)
    elif uploaded_file.name.endswith(".txt"):
        loader = TextLoader(temp_path, encoding="utf-8")
    else:
        st.error("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")
        return None

    documents = loader.load()

    # Clean up the temporary file
    os.remove(temp_path)

    # Return extracted text
    return " ".join([doc.page_content for doc in documents])


# Step 4: Streamlit App
def main():
    st.set_page_config(page_title="Resume Parser with Gemini", layout="centered")
    st.title("📄 Resume Parser using LangChain + Gemini 2.5 Flash")

    uploaded_file = st.file_uploader("Upload your resume (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])

    if uploaded_file:
        with st.spinner("Reading and extracting text..."):
            resume_text = load_resume(uploaded_file)
            if not resume_text:
                st.error("Failed to load the resume.")
                return

        st.subheader("Resume Text Preview")
        st.text_area("Extracted Resume Text", value=resume_text[:4000], height=200)

        if st.button("Parse Resume with Gemini"):
            with st.spinner("Parsing resume using Gemini..."):
                formatted_prompt = prompt.format(resume_text=resume_text)
                response = llm.invoke(formatted_prompt)

                try:
                    parsed_json = json.loads(response.content)
                    st.success("✅ Resume parsed successfully!")
                    st.json(parsed_json)
                except json.JSONDecodeError:
                    st.warning("⚠️ The model returned non-JSON text. Here's the raw output:")
                    st.write(response.content)


# Entry point
if __name__ == "__main__":
    main()









