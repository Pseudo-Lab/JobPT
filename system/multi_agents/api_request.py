import requests
import uuid

API_URL = "http://localhost:8000/chat"
SESSION_ID = str(uuid.uuid4())

base_resume = (
    """
Contact
Joanna Drummond
Department of Computer Science, University of Toronto
Email: jdrummond@cs.toronto.edu

Education
	•	Ph.D. Computer Science, University of Toronto (expected Spring 2017)
	•	Advisors: Allan Borodin, Kate Larson
	•	GPA: 3.83
	•	M.S. Computer Science, University of Toronto (Spring 2013)
	•	Advisor: Craig Boutilier
	•	GPA: 3.93
	•	B.S. Computer Science and Mathematics, University of Pittsburgh (Dec 2010)
	•	Minor: Theatre Arts
	•	GPA: 3.73, Magna Cum Laude

Publications (selected)
	•	Strategy-Proofness in the Stable Matching Problem with Couples, AAMAS 2016
	•	SAT is an Effective and Complete Method for Solving Stable Matching Problems with Couples, IJCAI-15
	•	Preference Elicitation and Interview Minimization in Stable Matchings, AAAI-14
	•	Intrinsic and Extrinsic Evaluation…, NAACL 2012
	•	Evidence of Misunderstandings in Tutorial Dialogue and Their Impact on Learning, AIED 2009

Awards & Fellowships
	•	Microsoft Research PhD Fellowship Finalist (2016)
	•	Ontario Graduate Scholarship ($15,000), multiple years
	•	Google Anita Borg Scholarship Finalist (2012)
	•	NSF Graduate Research Fellowship Awardee (declined)
	•	DREU Research Program Recipient

Research Experience
	•	Microsoft Research Intern, Cloud Pricing (2016)
	•	University of Toronto RA
	•	Matching theory, multi-attribute preferences, social network matching
	•	University of Pittsburgh RA
	•	Student dialogue systems, engagement detection, machine learning
	•	USC ISI (DREU Program)
	•	Forum data classification using HMMs & decision trees

Teaching Experience
	•	TA, University of Toronto
	•	Intro to AI course, Python-based labs, assignments, exams
	•	TA, University of Pittsburgh
	•	College Algebra Recitation, tutoring from Algebra to Calculus III

Technical Skills
	•	Languages: Python, Java (proficient); Julia, R, Matlab, Bash (familiar)
	•	OS: Linux, macOS (proficient); Windows (familiar)
	•	Tools: LaTeX, Weka
            """,
)

jd = """
Meta is embarking on the most transformative change to its business and technology in company history, and our Machine Learning Engineers are at the forefront of this evolution. By leading crucial projects and initiatives that have never been done before, you have an opportunity to help us advance the way people connect around the world.
 
The ideal candidate will have industry experience working on a range of recommendation, classification, and optimization problems. You will bring the ability to own the whole ML life cycle, define projects and drive excellence across teams. You will work alongside the world’s leading engineers and researchers to solve some of the most exciting and massive social data and prediction problems that exist on the web.
Software Engineer, Machine Learning Responsibilities
Leading projects or small teams of people to help them unblock, advocating for ML excellence
Adapt standard machine learning methods to best exploit modern parallel environments (e.g. distributed clusters, multicore SMP, and GPU)
Develop highly scalable classifiers and tools leveraging machine learning, data regression, and rules based models
Suggest, collect and synthesize requirements and create effective feature roadmaps
Code deliverables in tandem with the engineering team
Minimum Qualifications
6+ years of experience in software engineering or a relevant field. 3+ years of experience if you have a PhD
2+ years of experience in one or more of the following areas: machine learning, recommendation systems, pattern recognition, data mining, artificial intelligence, or a related technical field
Experience with scripting languages such as Python, Javascript or Hack
Experience with developing machine learning models at scale from inception to business impact
Knowledge developing and debugging in C/C++ and Java, or experience with scripting languages such as Python, Perl, PHP, and/or shell scripts
Experience building and shipping high quality work and achieving high reliability
Track record of setting technical direction for a team, driving consensus and successful cross-functional partnerships
Experience improving quality through thoughtful code reviews, appropriate testing, proper rollout, monitoring, and proactive changes
Bachelor's degree in Computer Science, Computer Engineering, relevant technical field, or equivalent practical experience
Preferred Qualifications
Masters degree or PhD in Computer Science or another ML-related field
Exposure to architectural patterns of large scale software applications
Experience with scripting languages such as Pytorch and TF
For those who live in or expect to work from California if hired for this position, please click here for additional information.
About Meta
Meta builds technologies that help people connect, find communities, and grow businesses. When Facebook launched in 2004, it changed the way people connect. Apps like Messenger, Instagram and WhatsApp further empowered billions around the world. Now, Meta is moving beyond 2D screens toward immersive experiences like augmented and virtual reality to help build the next evolution in social technology. People who choose to build their careers by building with us at Meta help shape a future that will take us beyond what digital connection makes possible today—beyond the constraints of screens, the limits of distance, and even the rules of physics.

US$70.67/hour to US$208,000/year + bonus + equity + benefits

Individual compensation is determined by skills, qualifications, experience, and location. Compensation details listed in this posting reflect the base hourly rate, monthly rate, or annual salary only, and do not include bonus, equity or sales incentives, if applicable. In addition to base compensation, Meta offers benefits. Learn more about benefits at Meta. 

Equal Employment Opportunity
Meta is proud to be an Equal Employment Opportunity employer. We do not discriminate based upon race, religion, color, national origin, sex (including pregnancy, childbirth, reproductive health decisions, or related medical conditions), sexual orientation, gender identity, gender expression, age, status as a protected veteran, status as an individual with a disability, genetic information, political views or activity, or other applicable legally protected characteristics. You may view our Equal Employment Opportunity notice here.

Meta is committed to providing reasonable accommodations for qualified individuals with disabilities and disabled veterans in our job application procedures. If you need assistance or an accommodation due to a disability, fill out the Accommodations request form.
"""

test_cases = [
    {
        "messages": "내가 선택한 부분을 개선해줘, 영어 이력서니 이력서 부분은 영어로 답변해줘",
        "user_resume": """
Technical Skills
    •   Languages: Python, Java (proficient); Julia, R, Matlab, Bash (familiar)
    •   OS: Linux, macOS (proficient); Windows (familiar)
    •   Tools: LaTeX, Weka
        """,
        "resume": base_resume,
        "job_description": jd,
        "company_summary": "",
    },
    # 추가 케이스 필요시 여기에...
]

# 멀티턴 user input 시나리오 예시
multi_turn_inputs = [
    "내가 선택한 부분을 개선해줘, 영어 이력서니 이력서 부분은 영어로 답변해줘",
    "방금 답변한 부분을 한국어로 번역해줘.",
    "JD에 맞는 추가 경험을 추천해줘.",
]

# 첫 턴: 모든 컨텍스트 포함
payload = {
    "session_id": SESSION_ID,
    "messages": multi_turn_inputs[0],
    "user_resume": test_cases[0]["user_resume"],
    "resume": test_cases[0]["resume"],
    "job_description": test_cases[0]["job_description"],
    "company_summary": test_cases[0]["company_summary"],
}
response = requests.post(API_URL, json=payload)
print(f"[1] 질문: {multi_turn_inputs[0]}")
print("응답:", response.json().get("answer"))
print("=" * 40)

# 이후 턴: session_id와 messages만 전달 (필요시 resume 등도 추가 가능)
for i, user_input in enumerate(multi_turn_inputs[1:], start=2):
    payload = {
        "session_id": SESSION_ID,
        "messages": user_input,
    }
    response = requests.post(API_URL, json=payload)
    print(f"[{i}] 질문: {user_input}")
    print("응답:", response.json().get("answer"))
    print("=" * 40)
