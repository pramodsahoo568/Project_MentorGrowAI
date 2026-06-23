# run command
# streamlit run streamlit_ui_app.py
# ensure to set the OPENAI_API_KEY in the .streamlit/secrets.toml file

import streamlit as st
import  requests
import json
import os
import sys
from pathlib import Path
from datetime import datetime
import traceback


# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .concept-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #1f77b4;
    }
    .code-block {
        background-color: #263238;
        color: #aed581;
        padding: 1rem;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def render_header():
    """Render the main header."""
    st.markdown('<div class="main-header">🤖 Agentic AI: AWS Certification Mock test Assistant</div>', unsafe_allow_html=True)
    st.markdown("---")


def render_interactive_demo():
    """Render interactive demo."""
    st.header("🚀 Interactive Demo")

    st.markdown("""
    <div class="concept-box">
        <h3>Try the Production Agent</h3>
        <p>Execute the complete production system and see all patterns in action!</p>
    </div>
    """, unsafe_allow_html=True)

    # Demo configuration
    col1, col2 = st.columns(2)

    user_id = st.text_input("User ID:", value="demo_user@gmail.com")


    # User message input
    user_message = st.text_area(
        "Enter your request:",
        height=100
    )

    # Execute button, On button click
    if st.button("🚀 Execute Request", type="primary", use_container_width=True):

        with st.spinner("Processing request..."):

            try:
                response = requests.post(
                    "http://127.0.0.1:8000/generate-questions",
                    json={
                        "userId": user_id,
                        "message": user_message
                    },
                    timeout=100
                )

                if response.status_code == 200:

                    data = response.json()

                    # Backend returns JSON string inside "response"
                    parsed = json.loads(data["response"])
                    print("parsed response:", parsed)

                    intent = parsed.get("intent")
                    message = parsed.get("message")
                    questions = parsed.get("questions")

                    # ------------------------------
                    # UNKNOWN INTENT
                    # ------------------------------

                    if intent == "unknown":

                        st.warning(message)

                    # ------------------------------
                    # GENERATE QUESTIONS
                    # ------------------------------

                    elif intent == "generate_questions":

                        st.success("✅ Questions generated successfully!")

                        # Initialize session state
                        if "questions" not in st.session_state:
                            st.session_state.questions = questions

                        if "user_answers" not in st.session_state:
                            st.session_state.user_answers = {}

                        # Render questions
                        for idx, q in enumerate(st.session_state.questions):
                            st.markdown(f"### Q{idx + 1}. {q['question']}")

                            selected_option = st.radio(
                                label="Select your answer:",
                                options=q["options"],
                                key=f"question_{idx}"
                            )

                            st.session_state.user_answers[idx] = selected_option

                            st.markdown("---")

                    else:
                        st.warning("⚠️ Unknown response received from server.")

                else:
                    st.error(f"Server returned error: {response.status_code}")

            except Exception as e:
                st.error(f"Connection error: {str(e)}")


def load_ui():
    """Main application function."""
    render_header()
    render_interactive_demo()
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 2rem;">
            <p>Production LLM Agent Learning Platform | Built with Streamlit & LangChain</p>
            <p>For educational purposes - Class 3: Prompting That Ships + Production Foundations</p>
        </div>
        """, unsafe_allow_html=True)
    # Route to appropriate module



if __name__ == "__main__":
    load_ui()
