import os
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, DatabaseSessionService  # SQLite won't work on Vercel
from google.adk.tools import AgentTool, google_search
from google.genai import types

MODEL_NAME = "gemini-2.5-flash-lite"
APP_NAME = "meal_planner"

# FIX: Never hardcode keys. Read from environment.
# On Vercel/Railway you set these in the dashboard.
if not os.environ.get("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY environment variable is not set.")

retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)

planner_agent = Agent(
    name="PlannerAgent",
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    instruction="""You are a strict, analytical meal plan generator.
    Based on the user's goal, generate a structured, multi-day meal plan.
    Browse the web for accurate calorie and macro amounts using the google_search tool.
    You must create the plan according to South Indian cuisine.
    Do not add non-vegetarian meal options more than 2 times a week unless explicitly asked.
    The output must be clearly structured for breakfast, lunch, evening snacks, and dinner.
    Each meal entry must include: food name, serving size, calories, protein, carbs, fat.
    Also include the total macros for the entire day at the end.
    Format everything as a clean markdown table.
    """,
    tools=[google_search],
    output_key="main_meal_plan",
)

substitution_agent = Agent(
    name="SubstitutionAgent",
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    instruction="""You are a meal substitution agent.
    You will suggest alternatives to meals in the {main_meal_plan} when asked by the user.
    If the user says they have already eaten something not in the {main_meal_plan}, adjust the
    remaining meals of that day so that the daily macro targets are still met.
    Use the google_search tool to get accurate macro values for all foods.
    All suggestions must be based on South Indian cuisine.
    Return the response as a markdown table with columns: "Existing Plan" and "New Plan".
    """,
    tools=[google_search],
    output_key="substituted_meals",
)

coordination_agent = Agent(
    name="CoordinationAgent",
    model=Gemini(model=MODEL_NAME, retry_options=retry_config),
    instruction="""You are a coordination agent for a South Indian meal planning assistant.
    Analyse the user's query and route it to the correct agent:
    - New meal plan / diet plan / start planning → call PlannerAgent.
    - Substitutions / alternatives / already ate something off-plan → call SubstitutionAgent.
    After receiving the response, relay it clearly to the user.
    Always present meal or substitution data in well-formatted markdown tables.
    """,
    tools=[AgentTool(planner_agent), AgentTool(substitution_agent)],
    output_key="coordinator_response",
)

# InMemorySessionService: sessions live as long as the server process does.
# Fine for demos. For production, switch to DatabaseSessionService with a
# hosted Postgres URL (e.g. Neon or Supabase free tier).
# Use persistent DB if DATABASE_URL is set, otherwise fall back to in-memory
db_url = os.environ.get("DATABASE_URL")

if db_url:
    # Render gives a postgres:// URL but SQLAlchemy needs postgresql://
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    db_url = db_url.replace("?sslmode=require", "")
    session_service = DatabaseSessionService(db_url,connect_args={"ssl": True})
else:
    # Local development fallback
    session_service = InMemorySessionService()

runner = Runner(
    agent=coordination_agent,
    app_name=APP_NAME,
    session_service=session_service,
)