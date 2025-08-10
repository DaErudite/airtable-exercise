import os
from pyairtable import Api
from dotenv import load_dotenv
import json
from datetime import datetime, date

class CandidateShortlister:
    def __init__(self):
        self.api = Api(os.getenv('AIRTABLE_API_KEY'))
        self.base_id = os.getenv('AIRTABLE_BASE_ID')
        
        # Define tier-1 companies
        self.tier1_companies = {
            'Google', 'Meta', 'OpenAI', 'Microsoft', 'Apple', 
            'Amazon', 'Netflix', 'Tesla', 'Stripe', 'Airbnb'
        }
        
        # Define approved locations
        self.approved_locations = {
            'US', 'USA', 'United States', 'Canada', 'UK', 
            'United Kingdom', 'Germany', 'India'
        }
        
    def evaluate_candidate(self, applicant_id):
        # Get compressed JSON
        applicants = self.api.table(self.base_id, 'Applicants')
        records = applicants.all(formula=f"{{Applicant ID}} = '{applicant_id}'")
        
        if not records:
            return False, "Applicant not found"
            
        compressed_json = records[0]['fields'].get('Compressed JSON')
        if not compressed_json:
            return False, "No data found"
            
        try:
            data = json.loads(compressed_json)
        except:
            return False, "Invalid JSON data"
            
        # Evaluate criteria
        experience_pass, exp_reason = self.check_experience(data.get('experience', []))
        compensation_pass, comp_reason = self.check_compensation(data.get('salary', {}))
        location_pass, loc_reason = self.check_location(data.get('personal', {}))
        
        # Determine if shortlisted
        is_shortlisted = experience_pass and compensation_pass and location_pass
        
        # Create reason summary
        reasons = []
        if experience_pass:
            reasons.append(f"✓ Experience: {exp_reason}")
        else:
            reasons.append(f"✗ Experience: {exp_reason}")
            
        if compensation_pass:
            reasons.append(f"✓ Compensation: {comp_reason}")
        else:
            reasons.append(f"✗ Compensation: {comp_reason}")
            
        if location_pass:
            reasons.append(f"✓ Location: {loc_reason}")
        else:
            reasons.append(f"✗ Location: {loc_reason}")
            
        score_reason = "\n".join(reasons)
        
        # Update shortlist status
        applicants.update(records[0]['id'], {
            'Shortlist Status': 'Shortlisted' if is_shortlisted else 'Not Shortlisted'
        })
        
        # If shortlisted, create lead record
        if is_shortlisted:
            self.create_shortlisted_lead(applicant_id, compressed_json, score_reason)
            
        return is_shortlisted, score_reason
        
    def check_experience(self, experience_list):
        if not experience_list:
            return False, "No work experience provided"
            
        # Check for tier-1 companies
        for exp in experience_list:
            company = exp.get('company', '').strip()
            if company in self.tier1_companies:
                return True, f"Worked at tier-1 company: {company}"
                
        # Calculate total years of experience
        total_years = 0
        for exp in experience_list:
            start = exp.get('start_date')
            end = exp.get('end_date')
            
            if start and end:
                try:
                    start_date = datetime.strptime(start, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end, '%Y-%m-%d').date()
                    years = (end_date - start_date).days / 365.25
                    total_years += years
                except:
                    # If date parsing fails, estimate 2 years per role
                    total_years += 2
                    
        if total_years >= 4:
            return True, f"Has {total_years:.1f} years of experience"
        else:
            return False, f"Only {total_years:.1f} years of experience (need 4+)"
            
    def check_compensation(self, salary_data):
        preferred_rate = salary_data.get('preferred_rate', 0)
        availability = salary_data.get('availability', 0)
        
        rate_ok = preferred_rate <= 100
        availability_ok = availability >= 20
        
        if rate_ok and availability_ok:
            return True, f"Rate: ${preferred_rate}/hr, Availability: {availability}hrs/week"
        else:
            issues = []
            if not rate_ok:
                issues.append(f"Rate too high: ${preferred_rate}/hr (max $100)")
            if not availability_ok:
                issues.append(f"Low availability: {availability}hrs/week (min 20)")
            return False, "; ".join(issues)
            
    def check_location(self, personal_data):
        location = personal_data.get('location', '').strip()
        
        for approved in self.approved_locations:
            if approved.lower() in location.lower():
                return True, f"Located in approved region: {location}"
                
        return False, f"Location not approved: {location}"
        
    def create_shortlisted_lead(self, applicant_id, compressed_json, score_reason):
        leads_table = self.api.table(self.base_id, 'Shortlisted Leads')
        
        leads_table.create({
            'Applicant': applicant_id,
            'Compressed JSON': compressed_json,
            'Score Reason': score_reason
        })

# Usage
if __name__ == "__main__":
    shortlister = CandidateShortlister()
    is_shortlisted, reason = shortlister.evaluate_candidate("002")
    print(f"Shortlisted: {is_shortlisted}")
    print(f"Reason: {reason}")