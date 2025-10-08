from langchain.agents import create_agent
from weather_tools import fetch_weather, compare_weather, forecast_weather

weather_agent = create_agent(
    name="WeatherAgent",
    model="openai:gpt-4o-mini",
    prompt="Provide a brief weather update.",
    tools=[fetch_weather, compare_weather, forecast_weather]
)

def execute(prompt: str): 
    response = weather_agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    
    if (response['messages'] and response['messages'][-1]):
        message = response['messages'][-1]
        return message.content
    