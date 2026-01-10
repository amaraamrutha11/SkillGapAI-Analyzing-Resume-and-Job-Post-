import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt


# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="SkillGapAI Dashboard", layout="wide")

# ------------------ HEADER ------------------
st.markdown(
    """
    <h1 style='color:#1e3c72;'>📊 SkillGapAI – Dashboard & Report Export</h1>
    <p>Milestone-4: Dashboard and Report Export Module</p>
    <hr>
    """,
    unsafe_allow_html=True
)

# ================== DATA ==================
skills = ["Python", "Machine Learning", "TensorFlow", "SQL",
          "Statistics", "Communication", "AWS", "Project Mgmt"]

resume_scores = [90, 85, 80, 65, 78, 70, 30, 40]
job_scores = [95, 88, 75, 80, 85, 75, 85, 70]

matched_skills = ["Python", "Machine Learning"]
partial_skills = ["SQL"]
missing_skills = ["AWS", "Project Mgmt"]

# ================== SKILL MATCH OVERVIEW ==================
st.subheader("📈 Skill Match Overview")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### 72%\nOverall Match")
with c2:
    st.markdown("### 6\nMatched Skills")
with c3:
    st.markdown("### 4\nMissing Skills")

st.markdown("---")

# ================== RESUME VS JOB BAR CHART ==================
df_bar = pd.DataFrame({
    "Skill": skills,
    "Resume Skills": resume_scores,
    "Job Requirements": job_scores
})

bar_df = df_bar.melt("Skill", var_name="Type", value_name="Score")

bar_chart = alt.Chart(bar_df).mark_bar(height=18).encode(
    y=alt.Y("Skill:N", sort="-x", title=None),
    x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Match Percentage"),
    color=alt.Color(
        "Type:N",
        scale=alt.Scale(range=["#4A90E2", "#7CB342"]),
        legend=alt.Legend(title="")
    ),
    tooltip=["Skill", "Score", "Type"]
).properties(height=300)

st.altair_chart(bar_chart, use_container_width=True)

# ================== CIRCULAR METRICS (TEXT VERSION) ==================
c4, c5, c6, c7 = st.columns(4)
c4.metric("Python", "92%")
c5.metric("Machine Learning", "88%")
c6.metric("SQL", "65%")
c7.metric("AWS", "30%")

st.markdown("---")

# ================== SKILL COMPARISON + ROLE VIEW ==================
left, right = st.columns([2, 1])

with left:
    st.subheader("⚖️ Skill Comparison")

    def progress(label, value):
        st.markdown(f"**{label}**")
        st.progress(value / 100)

    progress("Python", 92)
    progress("Machine Learning", 88)
    progress("SQL", 65)

with right:
    st.subheader("👤 Role View")
    role = st.radio("", ["Job Seeker", "Recruiter"], horizontal=True)

    categories = ["Technical Skills", "Soft Skills", "Experience", "Education", "Certifications"]
    current_profile = [80, 70, 65, 75, 60]
    job_requirements = [90, 85, 80, 70, 85]

    N = len(categories)

    angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
    angles = np.concatenate([angles, [angles[0]]])

    current_profile = current_profile + [current_profile[0]]
    job_requirements = job_requirements + [job_requirements[0]]

    fig, ax = plt.subplots(figsize=(4.5, 4.5), subplot_kw=dict(polar=True))

    # 🔹 Make radar start from top
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # 🔹 Draw polygon grid (THIS IS THE KEY FIX)
    ax.set_thetagrids(np.degrees(angles[:-1]), categories)
    ax.set_rlabel_position(0)
    ax.set_ylim(0, 100)

    for grid in [20, 40, 60, 80, 100]:
        ax.plot(angles, [grid]*len(angles), color="gray", linewidth=0.4, alpha=0.4)

    # 🔹 Plot data
    ax.plot(angles, current_profile, color="#4A90E2", linewidth=2, label="Current Profile")
    ax.fill(angles, current_profile, color="#4A90E2", alpha=0.25)

    ax.plot(angles, job_requirements, color="#7CB342", linewidth=2, label="Job Requirements")
    ax.fill(angles, job_requirements, color="#7CB342", alpha=0.25)

    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))
    ax.set_title("Role Skill Comparison", pad=20)

    st.pyplot(fig)


# ================== UPSKILLING RECOMMENDATIONS ==================
st.subheader("💡 Upskilling Recommendations")

u1, u2, u3 = st.columns(3)
with u1:
    st.info("☁️ **AWS Cloud Services**\n\nComplete AWS Certified Solutions Architect course")
with u2:
    st.info("📊 **Advanced Statistics**\n\nEnroll in Advanced Statistics for Data Science")
with u3:
    st.info("📋 **Project Management**\n\nConsider PMP certification for leadership skills")

st.markdown("---")

# ================== CSV EXPORT ==================
st.subheader("📥 Download CSV Report")

report_df = pd.DataFrame({
    "Skill": skills,
    "Resume Score": resume_scores,
    "Job Requirement Score": job_scores
})

csv = report_df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", csv, "skill_gap_report.csv", "text/csv")

# ================== PDF EXPORT ==================
st.subheader("📄 Download PDF Report")

def clean_text(text):
    return text.encode("latin-1", "ignore").decode("latin-1")

def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(0, 10, clean_text("SkillGapAI – Skill Gap Report"), ln=True)
    pdf.ln(5)

    for i in range(len(skills)):
        line = f"{skills[i]} | Resume: {resume_scores[i]} | Job: {job_scores[i]}"
        pdf.cell(0, 8, clean_text(line), ln=True)

    return pdf.output(dest="S").encode("latin-1")

pdf_data = generate_pdf()

st.download_button(
    "⬇️ Download PDF",
    pdf_data,
    "skill_gap_report.pdf",
    "application/pdf"
)
