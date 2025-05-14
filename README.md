# Explanation Of Code Of Agentic RAG

## 📦 1. Importing Required Libraries
    import chainlit as cl
👉 Imagine chainlit is like the chatroom host — it manages the UI for your chat application.


    from agents import Agent, Runner, AsyncOpenAI, set_default_openai_api
    from agents import set_default_openai_client, set_tracing_disabled

🧠 These are parts of the Agents SDK:

 * Agent: Think of this as your AI assistant’s brain.

 * Runner: The manager that sends questions to the assistant and brings back answers.

 * AsyncOpenAI: The messenger that connects to Gemini's API.

 * set_default_openai_client/api/tracing: These are settings for how your assistant behaves.

    
    from agents.tool import function_tool
🛠️ Allows us to wrap any custom function as a tool that your AI agent can use. Think of it as giving your assistant a special skill, like “reading files.”


    import os
    from dotenv import load_dotenv
📁 This helps your app read secret keys (like API keys) stored in a .env file. Real-world example: you don’t give your house key to everyone — you hide it in a safe spot (.env file).


    import mimetypes
    from pdfminer.high_level import extract_text
    import openpyxl
    import docx

These are file-reading tools:

 * mimetypes: Helps figure out what kind of file you're dealing with.

 * pdfminer, openpyxl, docx: These help read PDFs, Excel, and Word documents.


## 🔐 2. Loading Environment Variables

    load_dotenv()

💡 This tells Python to look for a .env file and load the secret keys from it into your system.


    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")

🚨 If the key to your AI assistant (Gemini) is missing, this code will stop everything and tell you to fix it.


    gemini_api_key = os.getenv('GEMINI_API_KEY')

📦 This line fetches your Gemini API key from the .env file and stores it in a variable.



## 🔌 3. Connecting to Gemini AI (Google’s LLM)

    set_tracing_disabled(False)

👁️ Turns on logging/tracking (temporarily) so we can see what’s happening behind the scenes.


    external_client = AsyncOpenAI(
        api_key=gemini_api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

🤝 This creates a connection between your app and the Gemini API. Think of it like calling a hotline to talk to an expert.



        set_default_openai_client(external_client)
        set_default_openai_api("chat_completions")
        set_tracing_disabled(True)

✅ These lines tell your app:

 * "This is the expert (Gemini) we’re using."

 * Turn off internal logs now that setup is done.


## 🛠️ 4. Defining a File Reading Tool

    @function_tool
    def file_reader(file_path: str) -> str:

🧠 This function is like giving your assistant a magnifying glass. It allows it to open and read any file you upload.


        mime_type, _ = mimetypes.guess_type(file_path)

🔍 Try to guess the file type — is it a PDF? Word doc? etc.


        if file_path.endswith(".pdf"):
            text = extract_text(file_path)
            return text or "No readable text found in PDF."

📄 If it’s a PDF, use pdfminer to extract its text.


        elif file_path.endswith(".xlsx") or "spreadsheet" in str(mime_type):
            ...
📊 If it’s Excel, open it with openpyxl, read each cell, and combine it into readable text.


        elif file_path.endswith(".docx") or "word" in str(mime_type):
            ...
📃 If it’s Word, use docx to read all the paragraphs and join them.


        elif file_path.endswith(".txt") or "text" in str(mime_type):
            ...
📜 If it’s a simple text file, read it normally with Python.


        else:
            return f"Unsupported file format: {file_path}"

⛔ If the file is not supported, show an error.


        except Exception as e:
            return f"An error occurred while reading the file: {str(e)}"

⚠️ Catch any problem (e.g., corrupted file) and return the error message.



## 🤖 5. Creating the Agent (AI Assistant)

    agent = Agent(
        name="ResearcherBot",
        instructions=(
            "You are a research assistant. "
            "Use 'file_reader' to extract content from files when the user mentions reading or analyzing a file. "
            "Always try to show the full content."
        ),
        tools=[file_reader],
        model="gemini-2.0-flash",
    )

🧠 This creates the AI Agent:

 * name: What we call it — like "ResearcherBot."

 * instructions: Tells the AI its role and how to act.

 * tools: Gives it the file_reader skill.

 * model: Uses Gemini 2.0 Flash, a super-fast AI brain from Google.


## 💬 6. Chat Handlers

    @cl.on_chat_start
    async def start():

🎬 This function runs when the user opens the chat.


        await cl.Message(content="# AGENTIC RAG").send()
🖼️ Show a title in the chat UI.



        files = await cl.AskFileMessage(
            content="Please upload a file to begin!",
            accept=["*/*"],
            max_size_mb=20,
            timeout=180,
        ).send()

📤 Ask the user to upload any file (max 20MB, 3-minute timeout).


        if files:
            file_path = files[0].path
            cl.user_session.set("file_path", file_path)
            await cl.Message(content=f"File uploaded: {files[0].name}").send()


✅ If a file was uploaded:

 * Store it in the user’s session.

 * Confirm upload.


        else:
            await cl.Message(content="No file uploaded. Please start over.").send()

❌ If no file uploaded, let the user know.


## 📨 7. Handling User Messages

    @cl.on_message
    async def main(message: cl.Message):

📥 This function runs when a user types a message.


        file_path = cl.user_session.get("file_path")
📂 Get the path of the uploaded file.


        if not file_path:
            await cl.Message(content="Please upload a file first.").send()
            return

❌ If no file was uploaded earlier, ask them to do that first.



        user_query = message.content
        full_query = f"The file is located here: {file_path}. {user_query}"

📝 Add the file info to the user's question so the assistant knows which file to refer to.


        result = await cl.make_async(Runner.run_sync)(agent, full_query)

⚡ Send the message to the agent, wait for its response.


        await cl.Message(content=result.final_output).send()

📤 Show the result in the chat.


## 🎯 Summary (Real-world analogy)
Imagine you walk into a digital research assistant’s office:

 * You say: “Hey, I need help analyzing this file.”

 * You upload the file.

 * The assistant opens it, reads it, understands your query, and gives a smart answer — powered by Google Gemini.

