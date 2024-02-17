import os
import sys
from langchain.sql_database import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import ChatOpenAI


OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DATABASE_FILE = os.environ["DATABASE_FILE"]
MODEL_NAME = os.environ["MODEL_NAME"]

db = SQLDatabase.from_uri(f"sqlite:///{DATABASE_FILE}")
# result = db.run("SELECT * FROM comprobantes LIMIT 12;", fetch="cursor")

llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
agent_executor = create_sql_agent(llm, db=db, agent_type="openai-tools", verbose=True)

if __name__ == '__main__':
    try:
        while True:
            query = input("Pregunta:")
            agent_executor.invoke(query)
    except KeyboardInterrupt:
        print('\nGoodbye!')
        sys.exit(0)
