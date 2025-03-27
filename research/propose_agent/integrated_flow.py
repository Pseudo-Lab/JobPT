import os
from typing import Dict, Any, List, Tuple
from openai import OpenAI
from langgraph.graph import StateGraph, END

# Import our agent modules
from modules.suggestion_agent import SuggestionAgent
from modules.review_llm import ReviewLLM

class IntegratedWorkflow:
    """
    Integrated workflow that combines the SuggestionAgent and ReviewLLM
    to create a complete multi-turn document improvement process.
    """
    
    def __init__(self):
        self.suggestion_agent = SuggestionAgent()
        self.review_llm = ReviewLLM()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build an integrated graph that connects the SuggestionAgent and ReviewLLM.
        """
        graph = StateGraph(Dict)
        
        # Add nodes for the suggestion agent process
        graph.add_node("suggestion_process", self.run_suggestion_agent)
        
        # Add nodes for the review process
        graph.add_node("review_process", self.run_review_llm)
        
        # Add edge from suggestion to review
        graph.add_edge("suggestion_process", "review_process")
        
        # Add conditional edge from review to either end or back to suggestion
        graph.add_conditional_edges(
            "review_process",
            self.should_refine,
            {
                "refine": "suggestion_process",
                "complete": END
            }
        )
        
        # Set entry point
        graph.set_entry_point("suggestion_process")
        
        return graph.compile()
    
    def run_suggestion_agent(self, state: Dict) -> Dict:
        """
        Run the suggestion agent on the document.
        """
        document = state.get("document", "")
        feedback = state.get("feedback", "")
        
        # If we have feedback from a previous review, include it
        if feedback:
            document = f"{document}\n\nFeedback from review: {feedback}"
        
        # Run the suggestion agent
        result = self.suggestion_agent.run(document)
        
        # Return the modified document and other state
        return {
            **state,
            "modified_document": result.get("modified_doc", ""),
            "jd_info": result.get("jd_info", ""),
            "latest_info": result.get("latest_info", "")
        }
    
    def run_review_llm(self, state: Dict) -> Dict:
        """
        Run the review LLM on the modified document.
        """
        modified_document = state.get("modified_document", "")
        
        # Run the review LLM
        result = self.review_llm.run(modified_document)
        
        # Return the review results and other state
        return {
            **state,
            "grammar_report": result.get("grammar_report", ""),
            "ats_analysis": result.get("ats_analysis", ""),
            "jd_report": result.get("jd_report", ""),
            "review_complete": "<finish>" in result.get("jd_report", "")
        }
    
    def should_refine(self, state: Dict) -> str:
        """
        Determine if we should refine the document further or if we're done.
        """
        if state.get("review_complete", False):
            return "complete"
        else:
            # Extract feedback for the next iteration
            feedback = f"Grammar: {state.get('grammar_report', '')}\n"
            feedback += f"ATS: {state.get('ats_analysis', '')}\n"
            feedback += f"JD Report: {state.get('jd_report', '')}"
            
            # Update state with feedback
            state["feedback"] = feedback
            
            return "refine"
    
    def run(self, document: str) -> Dict:
        """
        Run the integrated workflow on a document.
        """
        initial_state = {"document": document}
        result = self.graph.invoke(initial_state)
        return result

# Example usage
if __name__ == "__main__":
    workflow = IntegratedWorkflow()
    document = """
    I am a software engineer with 5 years of experience in Python and JavaScript.
    I have worked on web applications and machine learning projects.
    """
    
    result = workflow.run(document)
    print("Final result:", result)
