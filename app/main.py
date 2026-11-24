from .agents import run_agent

if __name__ == "__main__":
    question = "What evidence supports RTK and non-RTK kinase redundancy in breast cancer resistance?"
    result = run_agent(question)
    print(result)
