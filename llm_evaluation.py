import os
from pyairtable import Api
from dotenv import load_dotenv
import json
import google.generativeai as genai
import time
import re

class LLMEvaluator:
    def __init__(self):
        self.api = Api(os.getenv('AIRTABLE_API_KEY'))
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        
        # Configure Gemini
        genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Free model
        
    def evaluate_applicant(self, applicant_id, max_retries=3):
        # Get compressed JSON
        applicants = self.api.table(self.base_id, 'Applicants')
        records = applicants.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        
        if not records:
            print(f"No applicant found: {applicant_id}")
            return False
            
        record = records[0]
        compressed_json = record['fields'].get('Compressed JSON')
        
        if not compressed_json:
            print(f"No JSON data for applicant: {applicant_id}")
            return False
            
        # Check if we already processed this data
        current_summary = record['fields'].get('LLM Summary', '')
        if current_summary:
            # Skip if already processed and JSON hasn't changed
            print(f"Already processed applicant: {applicant_id}")
            return True
            
        # Call LLM with retries
        for attempt in range(max_retries):
            try:
                result = self.call_llm(compressed_json)
                if result:
                    # Update Airtable with results
                    applicants.update(record['id'], {
                        'LLM Summary': result['summary'],
                        'LLM Score': result['score'],
                        'LLM Follow-Ups': result['follow_ups']
                    })
                    return True
                    
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep(2 ** attempt)
                    
        print(f"Failed to process applicant after {max_retries} attempts")
        return False
        
    def call_llm(self, json_data):
        prompt = f"""You are a recruiting analyst. Given this JSON applicant profile, do four things:

1. Provide a concise 75-word summary.
2. Rate overall candidate quality from 1-10 (higher is better).
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps.

Applicant Data:
{json_data}

Return exactly in this format:
Summary: <text>
Score: <integer>
Issues: <comma-separated list or 'None'>
Follow-Ups: <bullet list>"""

        try:
            # Generate content with Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.3,
                )
            )
            
            if response.text:
                return self.parse_llm_response(response.text)
            else:
                print("Gemini returned empty response")
                return None
            
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return None
            
    def parse_llm_response(self, content):
        try:
            # Extract sections using regex
            summary_match = re.search(r'Summary:\s*(.+?)(?=\n|Score:|$)', content, re.DOTALL)
            score_match = re.search(r'Score:\s*(\d+)', content)
            issues_match = re.search(r'Issues:\s*(.+?)(?=\n|Follow-Ups:|$)', content, re.DOTALL)
            followups_match = re.search(r'Follow-Ups:\s*(.+)$', content, re.DOTALL)
            
            return {
                'summary': summary_match.group(1).strip() if summary_match else "No summary generated",
                'score': int(score_match.group(1)) if score_match else 5,
                'issues': issues_match.group(1).strip() if issues_match else "None",
                'follow_ups': followups_match.group(1).strip() if followups_match else "No follow-ups suggested"
            }
            
        except Exception as e:
            print(f"Error parsing LLM response: {str(e)}")
            return {
                'summary': "Error processing response",
                'score': 0,
                'issues': "Processing error",
                'follow_ups': "Unable to generate follow-ups"
            }

# Usage
if __name__ == "__main__":
    load_dotenv()
    evaluator = LLMEvaluator()
    success = evaluator.evaluate_applicant("002")
    print(f"LLM evaluation {'successful' if success else 'failed'}")