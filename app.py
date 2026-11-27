import os
import json
import re
import streamlit as st
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

st.title("🎓 Student AI Assistant")
feature = st.sidebar.selectbox(
    "Choose a feature",
    ["AI Chatbot", "Summarize Notes", "Study Planner","Interview Preparation", "MCQ Generator", "Resume Analyzer", "My History"],
)

def ask(prompt, show=True):
    with st.spinner("Thinking..."):
        r = client.models.generate_content(model=MODEL, contents=prompt)
    st.write(r.text)

if feature == "AI Chatbot":
    q = st.text_area("Type your question")
    if st.button("Answer") and q:
        ask(f"Explain simply for a student: {q}")

elif feature == "Summarize Notes":
    notes = st.text_area("Paste your notes")
    if st.button("Summarize") and notes:
        ask(f"Summarize these notes in short bullet points: {notes}")

elif feature == "Study Planner":
    subjects = st.text_input("Subjects (comma separated)")
    c1, c2 = st.columns(2)
    days = c1.number_input("Days until exam", 1, 90, 7)
    hours = c2.number_input("Study hours per day", 1, 12, 3)
    if st.button("Create Plan") and subjects:
        ask(f"Make a day-by-day study plan for these subjects: {subjects}. "
            f"I have {days} days and {hours} hours per day. "
            "Include short breaks and a revision day at the end.")

elif feature == "Interview Preparation":
    topic = st.text_input("Enter a subject or interview topic")
    if st.button("Prepare Me") and topic:
        ask(f"Prepare beginner-friendly interview questions and answers about {topic}")

elif feature == "MCQ Generator":
    st.title("📝 MCQ Generator")

    topic = st.text_input("Enter a topic")

    count = st.slider("Number of Questions", 1, 20, 5)

    difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"]
    )

    if st.button("Generate MCQs"):
        if topic:
            prompt = f"""
            Generate {count} multiple choice questions about {topic}.
            Difficulty: {difficulty}.

            Return ONLY valid JSON in this format:
            [
                {{
                    "question": "Question here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer": "Correct option",
                    "explanation": "Explanation here"
                }}
            ]
            """

            with st.spinner("Generating questions..."):
                response = client.models.generate_content(
                    model=MODEL,
                    contents=prompt
                )

            try:
                result = response.text.strip()
                result = result.replace("```json", "").replace("```", "").strip()

                questions = json.loads(result)

                st.session_state.questions = questions
                st.session_state.submitted = False

            except Exception:
                st.error("Unable to generate quiz. Please try again.")

    if "questions" in st.session_state:

        st.subheader("Your Quiz")

        with st.form("quiz_form"):

            answers = {}

            for i, q in enumerate(st.session_state.questions):

                st.write(f"**Q{i+1}. {q['question']}**")

                answers[i] = st.radio(
                    "Select your answer:",
                    q["options"],
                    key=f"question_{i}",
                    index=None
                )

                st.divider()

            submitted = st.form_submit_button("Submit Quiz")

        if submitted:
            if any(answer is None for answer in answers.values()):
                st.warning("Please answer all questions before submitting.")

            else:
                score = 0

                for i, q in enumerate(st.session_state.questions):
                    if answers[i] == q["answer"]:
                        score += 1

                st.session_state.score = score
                st.session_state.submitted = True

        if st.session_state.get("submitted", False):

            score = st.session_state.score
            total = len(st.session_state.questions)

            st.success(f"Your Score: {score}/{total}")

            st.progress(score / total)

            for i, q in enumerate(st.session_state.questions):

                st.write(f"**Q{i+1}. {q['question']}**")
                st.write(f"Your Answer: {answers[i] if 'answers' in locals() else 'See below'}")
                st.write(f"Correct Answer: {q['answer']}")
                st.info(q["explanation"])
elif feature == "Resume Analyzer":
    st.subheader("Resume Analyzer")
    file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    job = st.text_input("Target job role (optional)")
    if file and st.button("Analyze"):
        from pypdf import PdfReader
        text = "".join(p.extract_text() or "" for p in PdfReader(file).pages)
        prompt = f"""Analyze this resume for the role: {job or 'general'}.
Give: 1) strengths, 2) weaknesses, 3) missing skills,
4) ATS keyword suggestions, 5) a score out of 10.

Resume:
{text}"""
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        st.write(response.text)
elif feature == "My History":
    st.subheader("My History")
    if not st.session_state.history:
        st.info("Nothing here yet. Use another feature first.")
    for h in reversed(st.session_state.history):
        with st.expander(h["question"][:80]):
            st.write(h["answer"])
    if st.button("Clear history"):
        st.session_state.history = []
        st.rerun()
