from dotenv import load_dotenv
import agent


load_dotenv()

def run():
    prompt = input("Ask me about the weather: ")
    response = agent.execute(prompt)
    print(response)

run()