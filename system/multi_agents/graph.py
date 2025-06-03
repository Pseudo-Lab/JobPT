from multi_agents.states.states import State, get_session_state, end_session
from multi_agents.agent.summary_agent import summary_agent
from multi_agents.agent.suggestion_agent import suggest_agent
from multi_agents.agent.supervisor_agent import router, refine_answer
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
import asyncio


async def create_graph(state: State):
    builder = StateGraph(State)
    # Node 추가
    builder.add_node("supervisor", router)
    builder.add_node("summary_agent", summary_agent)
    builder.add_node("suggestion_agent", suggest_agent)
    builder.add_node("refine_answer", refine_answer)

    # Start → Supervisor
    builder.add_edge("__start__", "supervisor")

    # Supervisor가 유저 입력 보고 결정
    def route_supervisor(state: State):
        import json

        msg = state.messages[-1].content
        try:
            if isinstance(msg, str) and msg.strip().startswith("{"):
                seq = json.loads(msg).get("sequence", "")
            else:
                seq = msg
        except Exception:
            seq = msg
        if seq not in {"summary", "suggestion", "summary_suggestion", "END"}:
            seq = "END"
        state.route_decision = seq
        return seq

    builder.add_conditional_edges(
        source="supervisor",
        path=route_supervisor,
        path_map={
            "summary": "summary_agent",
            "suggestion": "suggestion_agent",
            "summary_suggestion": "summary_agent",
            "END": "refine_answer",  # END도 refine_answer로
        },
    )

    def route_after_summary(state: State):
        state.route_decision = state.messages[-2].content
        if state.route_decision == "summary_suggestion":
            return "suggestion_agent"
        else:
            return "refine_answer"

    builder.add_conditional_edges(
        source="summary_agent",
        path=route_after_summary,
        path_map={
            "suggestion_agent": "suggestion_agent",
            "refine_answer": "refine_answer",
        },
    )

    # suggestion_agent 끝나고 refine_answer로
    builder.add_edge("suggestion_agent", "refine_answer")
    # refine_answer 끝나고 항상 종료
    builder.add_edge("refine_answer", "__end__")

    return builder.compile(), state


# base_resume = (
#     """
# Contact
# Joanna Drummond
# Department of Computer Science, University of Toronto
# Email: jdrummond@cs.toronto.edu

# Education
# 	•	Ph.D. Computer Science, University of Toronto (expected Spring 2017)
# 	•	Advisors: Allan Borodin, Kate Larson
# 	•	GPA: 3.83
# 	•	M.S. Computer Science, University of Toronto (Spring 2013)
# 	•	Advisor: Craig Boutilier
# 	•	GPA: 3.93
# 	•	B.S. Computer Science and Mathematics, University of Pittsburgh (Dec 2010)
# 	•	Minor: Theatre Arts
# 	•	GPA: 3.73, Magna Cum Laude

# Publications (selected)
# 	•	Strategy-Proofness in the Stable Matching Problem with Couples, AAMAS 2016
# 	•	SAT is an Effective and Complete Method for Solving Stable Matching Problems with Couples, IJCAI-15
# 	•	Preference Elicitation and Interview Minimization in Stable Matchings, AAAI-14
# 	•	Intrinsic and Extrinsic Evaluation…, NAACL 2012
# 	•	Evidence of Misunderstandings in Tutorial Dialogue and Their Impact on Learning, AIED 2009

# Awards & Fellowships
# 	•	Microsoft Research PhD Fellowship Finalist (2016)
# 	•	Ontario Graduate Scholarship ($15,000), multiple years
# 	•	Google Anita Borg Scholarship Finalist (2012)
# 	•	NSF Graduate Research Fellowship Awardee (declined)
# 	•	DREU Research Program Recipient

# Research Experience
# 	•	Microsoft Research Intern, Cloud Pricing (2016)
# 	•	University of Toronto RA
# 	•	Matching theory, multi-attribute preferences, social network matching
# 	•	University of Pittsburgh RA
# 	•	Student dialogue systems, engagement detection, machine learning
# 	•	USC ISI (DREU Program)
# 	•	Forum data classification using HMMs & decision trees

# Teaching Experience
# 	•	TA, University of Toronto
# 	•	Intro to AI course, Python-based labs, assignments, exams
# 	•	TA, University of Pittsburgh
# 	•	College Algebra Recitation, tutoring from Algebra to Calculus III

# Technical Skills
# 	•	Languages: Python, Java (proficient); Julia, R, Matlab, Bash (familiar)
# 	•	OS: Linux, macOS (proficient); Windows (familiar)
# 	•	Tools: LaTeX, Weka
#             """,
# )

# jd = """
# Meta is embarking on the most transformative change to its business and technology in company history, and our Machine Learning Engineers are at the forefront of this evolution. By leading crucial projects and initiatives that have never been done before, you have an opportunity to help us advance the way people connect around the world.
 
# The ideal candidate will have industry experience working on a range of recommendation, classification, and optimization problems. You will bring the ability to own the whole ML life cycle, define projects and drive excellence across teams. You will work alongside the world’s leading engineers and researchers to solve some of the most exciting and massive social data and prediction problems that exist on the web.
# Software Engineer, Machine Learning Responsibilities
# Leading projects or small teams of people to help them unblock, advocating for ML excellence
# Adapt standard machine learning methods to best exploit modern parallel environments (e.g. distributed clusters, multicore SMP, and GPU)
# Develop highly scalable classifiers and tools leveraging machine learning, data regression, and rules based models
# Suggest, collect and synthesize requirements and create effective feature roadmaps
# Code deliverables in tandem with the engineering team
# Minimum Qualifications
# 6+ years of experience in software engineering or a relevant field. 3+ years of experience if you have a PhD
# 2+ years of experience in one or more of the following areas: machine learning, recommendation systems, pattern recognition, data mining, artificial intelligence, or a related technical field
# Experience with scripting languages such as Python, Javascript or Hack
# Experience with developing machine learning models at scale from inception to business impact
# Knowledge developing and debugging in C/C++ and Java, or experience with scripting languages such as Python, Perl, PHP, and/or shell scripts
# Experience building and shipping high quality work and achieving high reliability
# Track record of setting technical direction for a team, driving consensus and successful cross-functional partnerships
# Experience improving quality through thoughtful code reviews, appropriate testing, proper rollout, monitoring, and proactive changes
# Bachelor's degree in Computer Science, Computer Engineering, relevant technical field, or equivalent practical experience
# Preferred Qualifications
# Masters degree or PhD in Computer Science or another ML-related field
# Exposure to architectural patterns of large scale software applications
# Experience with scripting languages such as Pytorch and TF
# For those who live in or expect to work from California if hired for this position, please click here for additional information.
# About Meta
# Meta builds technologies that help people connect, find communities, and grow businesses. When Facebook launched in 2004, it changed the way people connect. Apps like Messenger, Instagram and WhatsApp further empowered billions around the world. Now, Meta is moving beyond 2D screens toward immersive experiences like augmented and virtual reality to help build the next evolution in social technology. People who choose to build their careers by building with us at Meta help shape a future that will take us beyond what digital connection makes possible today—beyond the constraints of screens, the limits of distance, and even the rules of physics.

# US$70.67/hour to US$208,000/year + bonus + equity + benefits

# Individual compensation is determined by skills, qualifications, experience, and location. Compensation details listed in this posting reflect the base hourly rate, monthly rate, or annual salary only, and do not include bonus, equity or sales incentives, if applicable. In addition to base compensation, Meta offers benefits. Learn more about benefits at Meta. 

# Equal Employment Opportunity
# Meta is proud to be an Equal Employment Opportunity employer. We do not discriminate based upon race, religion, color, national origin, sex (including pregnancy, childbirth, reproductive health decisions, or related medical conditions), sexual orientation, gender identity, gender expression, age, status as a protected veteran, status as an individual with a disability, genetic information, political views or activity, or other applicable legally protected characteristics. You may view our Equal Employment Opportunity notice here.

# Meta is committed to providing reasonable accommodations for qualified individuals with disabilities and disabled veterans in our job application procedures. If you need assistance or an accommodation due to a disability, fill out the Accommodations request form.
# """


# async def main():
#     graph = await create_graph()
#     test_cases = [
#         # {"desc": "END", "messages": "Hi", "user_resume": ""},
#         # {
#         #     "desc": "summary",
#         #     "messages": "Summary this company",
#         #     "user_resume": "Acme Corp is a global leader in financial technology, providing innovative payment solutions and digital banking platforms to millions of users worldwide. Founded in 2001, Acme has offices in 20 countries and is recognized for its strong commitment to security and customer service.",
#         #     "job_description": "",
#         # },
#         {
#             "messages": "내가 선택한 부분을 개선해줘, 영어 이력서니 이력서 부분은 영어로 답변해줘",
#             "user_resume": """
# Technical Skills
# 	•	Languages: Python, Java (proficient); Julia, R, Matlab, Bash (familiar)
# 	•	OS: Linux, macOS (proficient); Windows (familiar)
# 	•	Tools: LaTeX, Weka
#             """,
#             "resume": base_resume,
#             "job_description": jd,
#             "company_summary": "",
#         },
#         {
#             "messages": "병렬환경(GPU 등), 대규모 분산 환경 관련 경험 강조",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Research Experience
# • Microsoft Research Intern – Investigated pricing mechanisms in cloud computing environments
# • Research Assistant – Explored stable matching on social networks and preference elicitation""",
#         },
#         {
#             "messages": "협업과 코딩 스킬 강조, 교육경험을 기술적 관점에서 개선",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Teaching Experience
# • TA, University of Toronto – Led weekly programming labs, assisted students in Python-based AI course
# • TA, University of Pittsburgh – Taught algebra recitations, supported student problem-solving""",
#         },
#         {
#             "messages": "Python/Java 역량에 실전 프로젝트 경험 추가",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Technical Skills
# • Languages: Python, Java (proficient); Julia, R, Matlab, Bash (familiar)
# • Tools: LaTeX, Weka""",
#         },
#         {
#             "messages": "LaTeX, Weka 등 툴을 ML 개발툴 관점에서 확장 설명 유도",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Technical Skills
# • Tools: LaTeX for academic paper writing; Weka for machine learning experiments""",
#         },
#         {
#             "messages": "AI 과목 조교 경험을 실무적 스킬로 전환",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Teaching Experience
# • Helped develop assignments, created marking schemes, and held lab sessions in Python for upper-level AI course.""",
#         },
#         {
#             "messages": "논문 경험 중 classification/recommendation 관련 성과 강조",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Publications
# • Preference Elicitation and Interview Minimization in Stable Matchings, AAAI-14
# • Intrinsic and Extrinsic Evaluation of an Automatic User Disengagement Detector, NAACL 2012""",
#         },
#         {
#             "messages": "PhD 연구 경험을 ML lifecycle에 맞춰 재표현",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Education
# • Ph.D. Computer Science – Focused on algorithmic game theory, multi-agent systems, and matching markets""",
#         },
#         {
#             "messages": "도구 위주의 나열형 스킬을 실전 활용 중심으로 개선",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Technical Skills
# • Familiar with Git for version control, Bash scripting for automation, and Docker for environment consistency""",
#         },
#         {
#             "messages": "논문 경력을 실전 문제 해결력과 연결되게 개선",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Publications
# • SAT is an Effective and Complete Method for Solving Stable Matching Problems with Couples, IJCAI-15""",
#         },
#         {
#             "messages": "C++/Java 등 시스템 수준 언어 활용 가능성 유도",
#             "job_description": jd,
#             "company_summary": "",
#             "resume": base_resume,
#             "user_resume": """Technical Skills
# • Languages: Python, Java (proficient); experience with low-level systems courses involving C/C++""",
#         },
#     ]
#     for case in test_cases:
#         print(f"유저 질문: {case['messages']}")
#         print(f"유저 선택 부분: {case['user_resume']}")

#         state = {
#             "messages": case["messages"],
#             "user_resume": case["user_resume"],
#             "job_description": case["job_description"],
#             "company_summary": case["company_summary"],
#             "resume": case["resume"],
#         }
#         result = await graph.ainvoke(state)
#         print("최종 답변")
#         print(result["messages"][-1].content)
#         print()
#         print("========================================")


# if __name__ == "__main__":
#     asyncio.run(main())
