"""
agent.py
Mahdi's AI Digital Twin Agent.
Uses OpenAI Agents SDK with Google Gemini (OpenAI-compatible endpoint).
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from cv_loader import get_cv_summary
from tools import record_user_email, record_unanswered_question

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).parent
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def get_system_prompt() -> str:
    """Builds the system prompt with Mahdi's CV summary injected."""
    summary = get_cv_summary()
    return f"""
# Your role

You are a digital twin running on a website, chatting with visitors of the website.
You represent the person who's website you are on.
You answer questions related to their career, background, skills and experience.

Here are the details of the person you are representing:

{summary}

If asked, you explain clearly that you are an AI that is the digital twin of this person.

# Rules

Engage with the user. Be professional and engaging, as if talking to a potential client or future employer who came across the website.
Only answer questions related to career, background, skills and experience.
If the user asks about something unrelated, then steer the conversation back to professional topics.

Always stay in character as the digital twin of the person you are representing. Represent the person.

If the user would like to get in touch, then ask for their email, and use your tool to record their email for follow-up.

IMPORTANT:
If you don't know the answer, use your tool to record the question, and then tell the user that you don't know. Never make up an answer.
""".strip()


# Tool definitions in OpenAI function schema format
TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "record_user_email",
            "description": "Records the visitor's email address and inquiry notes for follow-up by Mahdi.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "The user's email address (e.g. user@example.com)",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes or details about what they want to discuss",
                    },
                },
                "required": ["email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_unanswered_question",
            "description": "Records a question the digital twin does not know the answer to, so Mahdi can review it later.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The unanswered question asked by the user",
                    },
                    "context": {
                        "type": "string",
                        "description": "Context or topic of the question",
                    },
                },
                "required": ["question"],
            },
        },
    },
]

AVAILABLE_TOOLS = {
    "record_user_email": record_user_email,
    "record_unanswered_question": record_unanswered_question,
}


async def ask_agent(message: str, history: list = None) -> str:
    """
    Main entrypoint to chat with the digital twin.
    Supports chat history formatted as:
    [{"role": "user"|"assistant", "content": "..."}] or [[user_msg, bot_msg], ...]
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return (
            "⚠️ Gemini API Key not found.\n\n"
            "Please create a `.env` file inside the `ai-agent` directory with:\n"
            "`GEMINI_API_KEY=your_actual_key`\n\n"
            "You can get a free key from Google AI Studio (https://aistudio.google.com/)."
        )

    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        base_url=GEMINI_BASE_URL,
        api_key=api_key,
    )

    system_prompt = get_system_prompt()

    # Normalize messages
    messages = [{"role": "system", "content": system_prompt}]

    if history:
        for item in history:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                user_text, assistant_text = item
                if user_text:
                    messages.append({"role": "user", "content": str(user_text)})
                if assistant_text:
                    messages.append({"role": "assistant", "content": str(assistant_text)})
            elif isinstance(item, dict) and "role" in item and "content" in item:
                messages.append(item)

    # Add current user message
    messages.append({"role": "user", "content": message})

    # Call Gemini model with tool calling support
    try:
        response = await client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=messages,
            tools=TOOLS_SPEC,
            tool_choice="auto",
            temperature=0.7,
        )

        choice = response.choices[0]
        response_message = choice.message

        # Handle tool calling if triggered by the model
        if response_message.tool_calls:
            # Append the assistant's tool call message
            messages.append(response_message)

            for tool_call in response_message.tool_calls:
                func_name = tool_call.function.name
                func_args = {}
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except Exception:
                    func_args = {}

                tool_func = AVAILABLE_TOOLS.get(func_name)
                if tool_func:
                    tool_result = tool_func(**func_args)
                else:
                    tool_result = f"Error: Tool '{func_name}' not found."

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result),
                })

            # Send back tool results to complete the conversational response
            followup = await client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                temperature=0.7,
            )
            return followup.choices[0].message.content or "Done."

        return response_message.content or "I am here to help answer questions about Mahdi's background and experience."

    except Exception as e:
        error_str = str(e)
        print(f"[Agent Error] {error_str}")
        if "401" in error_str or "API_KEY" in error_str.upper():
            return "⚠️ Authentication error with Google Gemini API Key. Please verify that your `GEMINI_API_KEY` is correct in `.env`."
        return f"Sorry, I encountered an issue while processing your request: {error_str}"

