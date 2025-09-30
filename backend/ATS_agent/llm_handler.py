import os
import openai
from dotenv import load_dotenv


class LLMHandler:
    def __init__(self):
        self.llm_call_count = 0
        self.total_tokens = 0
        self._load_api_keys()

    def _load_api_keys(self):
        env_paths = []

        try:
            env_paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
        except:
            pass

        try:
            env_paths.append('/mnt/e/code/GJS/JobPT-main/research/validate_agent/.env')
        except:
            pass

        env_file_path = None
        for path in env_paths:
            if os.path.exists(path):
                env_file_path = path
                break

        if not env_file_path:
            default_path = env_paths[0] if env_paths else '.env'
            print(f"Warning: .env file not found. Creating default at {default_path}")
            self._create_default_env(default_path)
            env_file_path = default_path

        load_dotenv(env_file_path)

    def _create_default_env(self, path):
        with open(path, 'w') as f:
            f.write("# API Keys for ATS Analyzer\n")
            f.write("# Replace with your actual API keys\n\n")
            f.write("# OpenAI API Key\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n\n")
            f.write("# Groq API Key (optional, only needed if using model=2)\n")
            f.write("GROQ_API_KEY=your_groq_api_key_here\n\n")
            f.write("# Gemini API Key (optional, only needed if using model=3)\n")
            f.write("GEMINI_API_KEY=your_gemini_api_key_here\n")

    def call_llm(self, prompt, model=1, language='en'):
        try:
            system_prompt = "You are an expert resume analyst and ATS specialist."
            if language == 'ko':
                system_prompt += " 모든 답변은 한국어로 제공하되, 지시된 용어 형식을 유지하세요."

            if model == 1:
                return self._call_openai(prompt, system_prompt)
            elif model == 2:
                return self._call_groq(prompt, system_prompt)
            elif model == 3:
                return self._call_gemini(prompt, system_prompt)
            else:
                return "Error: Invalid model selection"

        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return self._generate_dummy_response(prompt)

    def _call_openai(self, prompt, system_prompt):
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key or openai_api_key == "your_openai_api_key_here":
            print("Error: OpenAI API key not found or not set in .env file")
            print("Attempting to use alternative model...")
            return self._generate_dummy_response(prompt)

        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )

        self.llm_call_count += 1
        self.total_tokens += response.usage.total_tokens
        return response.choices[0].message.content.strip()

    def _call_groq(self, prompt, system_prompt):
        try:
            from groq import Groq
        except ImportError:
            print("Error: Groq package not installed. Please install it with 'pip install groq'")
            print("Falling back to OpenAI API...")
            return self._call_openai(prompt, system_prompt)

        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key or groq_api_key == "your_groq_api_key_here":
            print("Error: Groq API key not found or not set in .env file")
            print("Falling back to OpenAI API...")
            return self._call_openai(prompt, system_prompt)

        client = Groq(api_key=groq_api_key)
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_completion_tokens=1500,
            top_p=1,
            stream=False,
            stop=None,
        )

        self.llm_call_count += 1
        self.total_tokens += completion.usage.total_tokens
        return completion.choices[0].message.content.strip()

    def _call_gemini(self, prompt, system_prompt):
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key or gemini_api_key == "your_gemini_api_key_here":
            print("Error: Gemini API key not found or not set in .env file")
            print("Attempting to use OpenAI API instead...")
            return self._call_openai(prompt, system_prompt)

        client = openai.OpenAI(
            api_key=gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        response = client.chat.completions.create(
            model="gemini-2.0-flash-lite",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )

        self.llm_call_count += 1
        self.total_tokens += response.usage.total_tokens
        return response.choices[0].message.content.strip()

    def _generate_dummy_response(self, prompt):
        print("Generating dummy response for testing purposes...")

        if "keywords" in prompt.lower():
            return "This is a dummy keywords analysis.\n\nThe resume contains some keywords that match the job description, but could be improved by adding more specific technical skills and qualifications.\n\nScore: 65 points"
        elif "experience" in prompt.lower():
            return "This is a dummy experience analysis.\n\nThe candidate's experience partially matches the job requirements. Some areas could be strengthened to better align with the position.\n\nScore: 70 points"
        elif "format" in prompt.lower():
            return "This is a dummy format analysis.\n\nThe resume has a clean format but could be improved with better section organization and more consistent formatting.\n\nScore: 75 points"
        elif "content" in prompt.lower():
            return "This is a dummy content quality analysis.\n\nThe content is generally good but could use more quantifiable achievements and specific examples.\n\nScore: 68 points"
        elif "errors" in prompt.lower():
            return "This is a dummy errors analysis.\n\nThe resume has few grammatical errors but some inconsistencies in formatting and punctuation.\n\nScore: 80 points"
        elif "industry" in prompt.lower():
            return "This is a dummy industry analysis.\n\nThe resume shows good industry alignment but could benefit from more industry-specific terminology.\n\nScore: 72 points"
        elif "competitive" in prompt.lower():
            return "This is a dummy competitive analysis.\n\nThe resume is competitive but could be strengthened in areas of technical expertise and project outcomes.\n\nScore: 70 points"
        elif "improvements" in prompt.lower():
            return "This is a dummy improvement suggestions.\n\n1. Add more technical keywords from the job description\n2. Quantify achievements with specific metrics\n3. Improve formatting for better ATS readability"
        elif "final assessment" in prompt.lower():
            return "This is a dummy final assessment.\n\nThe resume is generally well-aligned with the job description but has room for improvement in keyword matching and experience presentation.\n\nFinal recommendation: Make minor improvements before applying."
        else:
            return "This is a dummy response for testing purposes. In a real scenario, this would contain a detailed analysis based on your prompt.\n\nScore: 70 points"

    def get_statistics(self):
        return {
            'llm_call_count': self.llm_call_count,
            'total_tokens': self.total_tokens
        }