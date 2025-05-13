

from agents import Agent, Runner, AsyncOpenAI,  set_default_openai_api
from agents import set_default_openai_client , set_tracing_disabled
from agents.tool import function_tool
import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")

gemini_api_key = os.getenv('GEMINI_API_KEY')
set_tracing_disabled(False)

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
set_default_openai_client(external_client)
set_default_openai_api("chat_completions")
set_tracing_disabled(True)

import mimetypes
import fitz  # PyMuPDF
import openpyxl
import docx

@function_tool
def file_reader(file_path: str) -> str:
    """
    Reads content from a given file path and returns its textual content.
    Supports PDF, Excel, Word, and plain text files.
    """
    try:
        mime_type, _ = mimetypes.guess_type(file_path)

        if file_path.endswith(".pdf"):
            doc = fitz.open(file_path)
            text = "\n".join([page.get_text() for page in doc])
            doc.close()
            return text or "No readable text found in PDF."

        elif file_path.endswith(".xlsx") or "spreadsheet" in str(mime_type):
            wb = openpyxl.load_workbook(file_path)
            content = []
            for sheet in wb.worksheets:
                for row in sheet.iter_rows(values_only=True):
                    content.append("\t".join([str(cell) if cell is not None else "" for cell in row]))
            return "\n".join(content) or "No readable text found in Excel."

        elif file_path.endswith(".docx") or "word" in str(mime_type):
            doc = docx.Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs]) or "No readable text found in Word document."

        elif file_path.endswith(".txt") or "text" in str(mime_type):
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        else:
            return f"Unsupported file format: {file_path}"

    except Exception as e:
        return f"An error occurred while reading the file: {str(e)}"


# Example usage
import asyncio

agent = Agent(
    name="ResearcherBot",
    instructions=(
        "You are a research assistant. "
        "Use 'web_search' for online queries. Use 'file_reader' to extract info from uploaded files. "
        "Do not summarize or modify tool outputs. Show maximum content. Include links where possible."
    ),
    tools=[file_reader],  # 👈 Added file_reader here
    model="gemini-2.0-flash",
)

query = "Read this file: file_reader('file.txt')"

result = Runner.run_sync(agent, query,)

print(result.final_output)






# web_agent: Agent = Agent(
#                           name="Web Agent",
#                           instructions="You only respond to website development related question",
#                           model="gemini-2.0-flash",
#                           handoff_description="Web Developer"
#                         )


# result = Runner.run_sync(web_agent, "tell me about web developer.",)


# print(result.final_output)