import os
from pyairtable import Api
from dotenv import load_dotenv
import json

load_dotenv()
class AirtableDecompressor:
    def __init__(self):
        
        self.api = Api(os.getenv('AIRTABLE_API_KEY'))
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
    def decompress_applicant_data(self, applicant_id):
        # Get the compressed JSON from Applicants table
        applicants = self.api.table(self.base_id, 'Applicants')
        records = applicants.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        
        if not records:
            print(f"No applicant found with ID: {applicant_id}")
            return False
            
        compressed_json = records[0]['fields'].get('Compressed JSON')
        if not compressed_json:
            print(f"No compressed JSON found for applicant: {applicant_id}")
            return False
            
        try:
            data = json.loads(compressed_json)
        except json.JSONDecodeError:
            print(f"Invalid JSON for applicant: {applicant_id}")
            return False
            
        # Update Personal Details
        self.update_personal_details(applicant_id, data.get('personal', {}))
        
        # Update Work Experience  
        self.update_work_experience(applicant_id, data.get('experience', []))
        
        # Update Salary Preferences
        self.update_salary_preferences(applicant_id, data.get('salary', {}))
        
        return True
        
    def update_personal_details(self, applicant_id, personal_data):
        table = self.api.table(self.base_id, 'Personal Details')
        
        # Check if record exists
        records = table.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        
        fields = {
            'Full Name': personal_data.get('name', ''),
            'Email': personal_data.get('email', ''),
            'Location': personal_data.get('location', ''),
            'LinkedIn': personal_data.get('linkedin', ''),
            'Applicant ID': applicant_id
        }
        
        if records:
            table.update(records[0]['id'], fields)
        else:
            table.create(fields)
            
    def update_work_experience(self, applicant_id, experience_data):
        table = self.api.table(self.base_id, 'Work Experience')
        
        # Delete existing records for this applicant
        existing = table.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        for record in existing:
            table.delete(record['id'])
            
        # Create new records
        for exp in experience_data:
            table.create({
                'Company': exp.get('company', ''),
                'Title': exp.get('title', ''),
                'Start Date': exp.get('start_date', ''),
                'End Date': exp.get('end_date', ''),
                'Technologies': exp.get('technologies', ''),
                'Applicant ID': applicant_id
            })
            
    def update_salary_preferences(self, applicant_id, salary_data):
        table = self.api.table(self.base_id, 'Salary Preferences')
        
        records = table.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        
        fields = {
            'Preferred Rate': salary_data.get('preferred_rate', 0),
            'Minimum Rate': salary_data.get('minimum_rate', 0),
            'Currency Type': salary_data.get('currency', 'USD'),
            'Availability': salary_data.get('availability', 0),
            'Applicant ID': applicant_id
        }
        
        if records:
            table.update(records[0]['id'], fields)
        else:
            table.create(fields)

# Usage
if __name__ == "__main__":
    decompressor = AirtableDecompressor()
    decompressor.decompress_applicant_data("002")
    print("Data decompressed successfully")