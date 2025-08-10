import os
from dotenv import load_dotenv
from compress_data import AirtableCompressor
from shortlist_candidates import CandidateShortlister
from llm_evaluation import LLMEvaluator

load_dotenv()

class ApplicationProcessor:
    def __init__(self):
        self.compressor = AirtableCompressor()
        self.shortlister = CandidateShortlister()
        self.llm_evaluator = LLMEvaluator()
        
    def process_applicant(self, applicant_id):
        print(f"Processing applicant: {applicant_id}")
        
        # Step 1: Compress data into JSON
        print("1. Compressing data...")
        data = self.compressor.get_applicant_data(applicant_id)
        success = self.compressor.update_applicant_json(applicant_id, data)
        
        if not success:
            print("❌ Failed to compress data")
            return False
            
        print("✅ Data compressed successfully")
        
        # Step 2: Evaluate for shortlisting
        print("2. Evaluating for shortlist...")
        is_shortlisted, reason = self.shortlister.evaluate_candidate(applicant_id)
        
        if is_shortlisted:
            print("✅ Candidate shortlisted!")
        else:
            print("⏸️ Candidate not shortlisted")
        print(f"Reason: {reason}")
        
        # Step 3: LLM evaluation
        print("3. Running LLM evaluation...")
        llm_success = self.llm_evaluator.evaluate_applicant(applicant_id)
        
        if llm_success:
            print("✅ LLM evaluation complete")
        else:
            print("❌ LLM evaluation failed")
            
        print(f"Processing complete for {applicant_id}")
        return True
        
    def process_all_applicants(self):
        """Process all applicants who have data but haven't been processed"""
        from pyairtable import Api
        
        api = Api(os.getenv('AIRTABLE_API_KEY'))
        applicants = api.table(os.getenv('AIRTABLE_BASE_ID'), 'Applicants')
        
        # Get all applicants
        records = applicants.all()
        
        for record in records:
            applicant_id = record['fields'].get('Applicant ID')
            compressed_json = record['fields'].get('Compressed JSON')
            
            if applicant_id and not compressed_json:
                print(f"\nProcessing unprocessed applicant: {applicant_id}")
                self.process_applicant(applicant_id)

# Usage
if __name__ == "__main__":
    processor = ApplicationProcessor()
    
    # Process specific applicant
    # processor.process_applicant("APP001")
    
    # Or process all unprocessed applicants
    processor.process_all_applicants()