from dotenv import load_dotenv
import core.agent as agent
import os

# Load .env from project root (parent directory of src)
load_dotenv()

def run():
    prompt = input("Ask me about the weather: ")
    response = agent.execute(prompt)
    print(response)

run()