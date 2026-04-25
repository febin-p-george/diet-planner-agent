import json
import uuid
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from google.genai import types

# Agents are imported once at module load — not per request.
from .agents import runner, session_service, APP_NAME


async def index(request):
    """Serves the chat UI."""
    return render(request, "chat/index.html")


@csrf_exempt
async def chat(request):
    """Receives a message, runs it through the ADK agent, returns the response."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST is allowed."}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    user_message = data.get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "Message cannot be empty."}, status=400)

    # Each browser tab gets its own session_id stored in localStorage.
    session_id = data.get("session_id") or str(uuid.uuid4())
    user_id = "web_user"

    # Get or create the ADK session for this conversation.
    try:
        session = await session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )
    except Exception:
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )

    content = types.Content(role="user", parts=[types.Part(text=user_message)])

    response_parts = []
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=content,
        ):
            if event.content and event.content.parts:
                text = event.content.parts[0].text
                if text and text.strip() and text != "None":
                    response_parts.append(text)
    except Exception as e:
        return JsonResponse({"error": f"Agent error: {str(e)}"}, status=500)

    # Deduplicate: the coordinator sometimes echoes sub-agent output.
    # Keep only the last non-empty part (the coordinator's final response).
    final_response = response_parts[-1] if response_parts else "Sorry, I couldn't generate a response."

    return JsonResponse({
        "response": final_response,
        "session_id": session_id,
    })