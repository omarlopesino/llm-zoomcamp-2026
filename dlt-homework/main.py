import sys

import logfire
from dotenv import load_dotenv

load_dotenv()

from agent import faq_agent, SearchDeps
from ingest import build_index, load_faq_data

logfire.configure()
logfire.instrument_pydantic_ai()

DEFAULT_QUESTION = 'I just discovered the course. Can I join it?'

def main():
    # Download the FAQ and build the search index
    documents = load_faq_data()
    index = build_index(documents)

    # Inject the index into the agent via the dependency container
    deps = SearchDeps(index=index)

    # Ask a question (from the CLI if provided). run_sync blocks until the agent
    # is done; the agent may call search multiple times before answering.
    question = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_QUESTION
    result = faq_agent.run_sync(question, deps=deps)

    print(result.output)

    # Make sure the spans are exported to Logfire before the process exits,
    # so the dlt pipeline can query them right away.
    logfire.force_flush()


if __name__ == '__main__':
    main()
