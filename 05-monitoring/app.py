import streamlit as st
from db import save_conversation, save_feedback
from assistant import create_assistant
from judge import evaluate_relevance

assistant = create_assistant()

st.title("Course Assistant")

user_input = st.text_input("Enter your question:")

if st.button("Ask"):
    with st.spinner("Processing..."):
        answer = assistant.rag(user_input)
        record = assistant.last_call
        conversation_id = save_conversation(record, user_input, "llm-zoomcamp")

    # Persist results so they survive the reruns triggered by the feedback buttons
    st.session_state.answer = answer
    st.session_state.record = record
    st.session_state.conversation_id = conversation_id
    st.session_state.feedback_given = None

if "answer" in st.session_state:
    st.success("Completed!")
    st.write(st.session_state.answer)

    # Show stats
    record = st.session_state.record
    st.write(f"Response time: {record.response_time:.2f}s")
    st.write(f"Prompt tokens: {record.prompt_tokens}")
    st.write(f"Completion tokens: {record.completion_tokens}")
    st.write(f"Cost: ${record.cost:.4f}")

    # LLM as a judge: calculate relevance and explanation.
    relevance, explanation = evaluate_relevance(user_input, answer)
    save_feedback(conversation_id, "judge",
                    relevance=relevance, explanation=explanation)
    st.write(f"Relevance: {relevance}")
    st.write(f"Explanation: {explanation}")

    # User feedback buttons.
    col1, col2 = st.columns(2)

    with col1:
        if st.button("+1"):
            save_feedback(st.session_state.conversation_id, "user", score=1)
            st.session_state.feedback_given = 1

    with col2:
        if st.button("-1"):
            save_feedback(st.session_state.conversation_id, "user", score=-1)
            st.session_state.feedback_given = -1

    if st.session_state.get("feedback_given") == 1:
        st.write("Thanks!")
    elif st.session_state.get("feedback_given") == -1:
        st.write("Thanks for the feedback!")


