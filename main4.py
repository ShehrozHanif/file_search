# Agentic RAG 

from agents import Agent, Runner, AsyncOpenAI, set_default_openai_api
from agents import set_default_openai_client, set_tracing_disabled
from agents.tool import function_tool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Validate Gemini API key
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY is not set. Please check your .env file.")

gemini_api_key = os.getenv("GEMINI_API_KEY")

# Set up Gemini API via proxy
set_tracing_disabled(False)
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)
set_default_openai_client(external_client)
set_default_openai_api("chat_completions")
set_tracing_disabled(True)

# -------------------------------
# 📄 File Reader Tool
# -------------------------------
import mimetypes
from pdfminer.high_level import extract_text
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
            text = extract_text(file_path)
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

# -------------------------------
# 🌐 Web Search Tool
# -------------------------------
import requests

SERP_API_KEY = "b2a52f67c0e31054e454b672b12bac22"
SERP_API_URL = "https://serpapi.abcproxy.com/search"

@function_tool
def web_search(query: str) -> str:
    """
    Performs a web search and returns clean markdown-formatted news results.
    """
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY,
        "num": 5,
        "fetch_mode": "static"
    }

    try:
        response = requests.get(SERP_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        organic_results = data.get("data", {}).get("organic_results", [])
        if not organic_results:
            return "No relevant news articles were found."

        formatted = ["**📰 Latest News**\n"]
        for i, result in enumerate(organic_results[:6]):
            title = result.get("title", "Untitled Article")
            snippet = result.get("snippet") or result.get("description") or "No summary available."
            link = result.get("url", "")
            source = result.get("source", "")

            formatted.append(
                f"**{i+1}. {title}**\n"
                f"*{snippet}*\n"
                f"Source: [{source}]({link})\n"
            )

        return "\n".join(formatted)

    except requests.exceptions.RequestException as e:
        return f"An error occurred with the web request: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

# -------------------------------
# 🤖 Agent Setup
# -------------------------------
agent = Agent(
    name="AgenticRAGBot",
    instructions=(
        "You are a smart assistant. Use `web_search` to get online information. "
        "Use `file_reader` to read uploaded files. Always show full tool outputs "
        "without summarizing unless asked. Help users get both local and web-based insights."
    ),
    tools=[file_reader, web_search],
    model="gemini-2.0-flash",
)

# -------------------------------
# ✅ Example: Reading a Local File
# -------------------------------
file_path = os.path.abspath("files\check.pdf")  # You can change this
query = f"The file is located here: {file_path}. Can you read this file and tell me the key points?"

result = Runner.run_sync(agent, query)

print("\n✅ Agent Output:\n")
print(result.final_output)


