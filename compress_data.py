

import os
from pyairtable import Api
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

class AirtableCompressor:
    def __init__(self):
        self.api = Api(os.getenv('AIRTABLE_API_KEY'))
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        
    def get_applicant_data(self, applicant_id):
        # Get data from all linked tables
        personal = self.api.table(self.base_id, 'Personal Details')
        experience = self.api.table(self.base_id, 'Work Experience') 
        salary = self.api.table(self.base_id, 'Salary Preferences')
        
        # Fetch records linked to this applicant
        personal_records = personal.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        experience_records = experience.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        salary_records = salary.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        
        # Build JSON structure
        data = {
            "personal": {},
            "experience": [],
            "salary": {}
        }
        
        if personal_records:
            p = personal_records[0]['fields']
            data["personal"] = {
                "name": p.get('Full Name', ''),
                "email": p.get('Email', ''),
                "location": p.get('Location', ''),
                "linkedin": p.get('LinkedIn', '')
            }
            
        for exp in experience_records:
            e = exp['fields']
            data["experience"].append({
                "company": e.get('Company', ''),
                "title": e.get('Title', ''),
                "start_date": e.get('Start Date', ''),
                "end_date": e.get('End Date', ''),
                "technologies": e.get('Technologies', '')
            })
            
        if salary_records:
            s = salary_records[0]['fields']
            data["salary"] = {
                "preferred_rate": s.get('Preferred Rate', 0),
                "minimum_rate": s.get('Minimum Rate', 0),
                "currency": s.get('Currency Type', 'USD'),
                "availability": s.get('Availability', 0)
            }
            
        return data
    
    def update_applicant_json(self, applicant_id, json_data):
        applicants = self.api.table(self.base_id, 'Applicants')
        
        # Find the applicant record
        records = applicants.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        
        if records:
            record_id = records[0]['id']
            applicants.update(record_id, {
                'Compressed JSON': json.dumps(json_data, indent=2)
            })
            return True
        return False

# Usage example
if __name__ == "__main__":
    compressor = AirtableCompressor()
    
    # Replace with actual applicant ID
    applicant_id = "001"
    data = compressor.get_applicant_data(applicant_id)
    compressor.update_applicant_json(applicant_id, data)
    print(f"Compressed data for {applicant_id}"+f"={data}")