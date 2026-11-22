import os
import streamlit as st
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

st.title("🎓 Student AI Assistant")
feature = st.sidebar.selectbox(
    "Choose a feature",
    ["AI Chatbot", "Summarize Notes", "Study Planner","Interview Preparation", "MCQ Generator"],
)

def ask(prompt):
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
    topic = st.text_input("Enter a topic")
    c1, c2, c3 = st.columns(3)
    n = c1.slider("Questions", 3, 10, 5)
    level = c2.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    fmt = c3.radio("Output", ["Quiz here", "PDF"])

    if st.button("Generate MCQs") and topic:
        prompt = f"""Create {n} {level} multiple choice questions about {topic}.
Return ONLY a JSON array, no other text. Each item must look like:
{{"question": "...", "options": ["...", "...", "...", "..."], "answer": "...", "explanation": "..."}}
Rules: exactly 4 options, no A/B/C/D prefixes, and "answer" must be exactly
the same text as one of the options."""
        with st.spinner("Creating your quiz..."):
            raw = generate(prompt)
        if raw:
            try:
                data = json.loads(re.search(r"\[.*\]", raw, re.S).group())
                for k in [k for k in st.session_state if k.startswith("mcq_")]:
                    del st.session_state[k]
                st.session_state["mcqs"] = data
                st.session_state["mcq_topic"] = topic
            except Exception:
                st.error("Could not read the questions. Please click Generate again.")

    mcqs = st.session_state.get("mcqs")
    if mcqs:
        if fmt == "PDF":
            t = st.session_state.get("mcq_topic", "quiz")
            st.success(f"{len(mcqs)} questions ready.")
            st.download_button(
                "📥 Download MCQs as PDF (with answer key)",
                data=make_pdf(f"MCQs: {t}", mcq_to_text(mcqs)),
                file_name=f"{t.replace(' ', '_')}_mcqs.pdf",
                mime="application/pdf",
            )
            with st.expander("Preview questions"):
                st.text(mcq_to_text(mcqs))
        else:
            with st.form("quiz"):
                for i, m in enumerate(mcqs):
                    st.radio(f"{i+1}. {m['question']}", m["options"],
                             index=None, key=f"mcq_{i}")
                submitted = st.form_submit_button("Submit Answers")
            if submitted:
                score = 0
                for i, m in enumerate(mcqs):
                    chosen = st.session_state.get(f"mcq_{i}")
                    if chosen and chosen.strip() == m["answer"].strip():
                        score += 1
                        st.success(f"Q{i+1}: Correct ✅")
                    else:
                        st.error(f"Q{i+1}: Wrong ❌  Correct answer: {m['answer']}")
                    st.caption(f"💡 {m.get('explanation', '')}")
                st.subheader(f"Your score: {score} / {len(mcqs)}")
                if score == len(mcqs):
                    st.balloons()
elif feature == "Resume Analyzer":
    st.header("📄 AI Resume Analyzer")
    st.write("Upload your resume and receive AI-powered feedback.")

    uploaded_file = st.file_uploader(
        "Upload your resume (PDF)",
        type=["pdf"]
    )

    if uploaded_file is not None:
        if st.button("Analyze Resume"):
            with st.spinner("Analyzing your resume..."):
                try:
                    pdf = PdfReader(io.BytesIO(uploaded_file.getvalue()))
                    resume_text = ""

                    for page in pdf.pages:
                        resume_text += page.extract_text() or ""

                    if not resume_text.strip():
                        st.error("No readable text found in this PDF.")
                    else:
                        prompt = f"""
                        Analyze this student resume.

                        Provide:
                        1. Overall rating out of 10.
                        2. Strengths.
                        3. Weaknesses.
                        4. Technical skills analysis.
                        5. Project improvement suggestions.
                        6. Education and internship feedback.
                        7. Suggestions to improve the resume.

                        Give simple and constructive feedback.
                        Do not invent qualifications or experience.

                        Resume:
                        {resume_text}
                        """

                        response = client.models.generate_content(
                            model=MODEL,
                            contents=prompt
                        )

                        st.subheader("📊 Resume Analysis")
                        st.markdown(response.text)

                except Exception as e:
                    st.error(f"Error analyzing resume: {e}")                    
