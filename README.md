# airtable-exercise
# Airtable Candidate Evaluation System Documentation

## Overview

This system automates the evaluation and shortlisting of job applicants using Airtable as the database backend, with Python scripts handling data compression, candidate evaluation, and LLM-powered analysis using Google's Gemini API.

## Architecture

The system consists of 5 main components:
- **Data Compression**: Consolidates applicant data from multiple tables into JSON
- **Candidate Shortlisting**: Automated evaluation based on predefined criteria
- **LLM Evaluation**: AI-powered candidate analysis and scoring
- **Data Decompression**: Expands compressed JSON back to normalized tables
- **Master Controller**: Orchestrates the entire pipeline

## Prerequisites

### Required Python Packages
```bash
pip install pyairtable python-dotenv google-generativeai
```

### Environment Variables
Create a `.env` file with:
```env
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_base_id
GOOGLE_API_KEY=your_gemini_api_key
```

## Airtable Base Structure

### Required Tables and Fields

#### 1. Applicants (Main Table)
- **Applicant ID** (Single line text) - Unique identifier
- **Compressed JSON** (Long text) - Consolidated applicant data
- **LLM Summary** (Long text) - AI-generated summary
- **LLM Score** (Number) - AI score (1-10)
- **LLM Follow-Ups** (Long text) - Suggested follow-up questions
- **Shortlist Status** (Single select: "Shortlisted", "Not Shortlisted")

#### 2. Personal Details
- **Applicant ID** (Single line text) - Links to main record
- **Full Name** (Single line text)
- **Email** (Email)
- **Location** (Single line text)
- **LinkedIn** (URL)

#### 3. Work Experience
- **Applicant ID** (Single line text) - Links to main record
- **Company** (Single line text)
- **Title** (Single line text)
- **Start Date** (Date)
- **End Date** (Date)
- **Technologies** (Long text)

#### 4. Salary Preferences
- **Applicant ID** (Single line text) - Links to main record
- **Preferred Rate** (Currency)
- **Minimum Rate** (Currency)
- **Currency Type** (Single select: "USD", "EUR", "GBP", etc.)
- **Availability** (Number) - Hours per week

#### 5. Shortlisted Leads (Auto-generated)
- **Applicant** (Single line text) - Applicant ID
- **Compressed JSON** (Long text) - Copy of applicant data
- **Score Reason** (Long text) - Detailed evaluation reasoning

## Script Documentation

### 1. Data Compression (`compress_data.py`)

**Purpose**: Consolidates applicant data from multiple normalized tables into a single JSON field for efficient processing.

**Key Functions**:
```python
def get_applicant_data(self, applicant_id):
    # Fetches data from Personal Details, Work Experience, and Salary Preferences
    # Returns structured JSON with nested objects and arrays
```

**Usage**:
```python
compressor = AirtableCompressor()
data = compressor.get_applicant_data("APP001")
compressor.update_applicant_json("APP001", data)
```

**JSON Structure**:
```json
{
  "personal": {
    "name": "John Doe",
    "email": "john@example.com",
    "location": "San Francisco, US",
    "linkedin": "linkedin.com/in/johndoe"
  },
  "experience": [
    {
      "company": "Google",
      "title": "Senior Engineer",
      "start_date": "2020-01-01",
      "end_date": "2023-12-31",
      "technologies": "Python, React, GCP"
    }
  ],
  "salary": {
    "preferred_rate": 85,
    "minimum_rate": 70,
    "currency": "USD",
    "availability": 40
  }
}
```

### 2. Data Decompression (`decompress.py`)

**Purpose**: Expands compressed JSON back to normalized table structure for data editing and management.

**Key Functions**:
```python
def decompress_applicant_data(self, applicant_id):
    # Reads JSON and populates Personal Details, Work Experience, and Salary tables
    # Handles record creation and updates automatically
```

**Usage**:
```python
decompressor = AirtableDecompressor()
decompressor.decompress_applicant_data("APP001")
```

**Important Notes**:
- Work Experience records are completely replaced (deleted and recreated)
- Personal Details and Salary Preferences are updated in place
- Handles missing or malformed JSON gracefully

### 3. Candidate Shortlisting (`shortlist_candidates.py`)

**Purpose**: Automated evaluation based on predefined business criteria.

**Evaluation Criteria**:

#### Experience Requirements (Either condition must be met):
- **Tier-1 Company Experience**: Google, Meta, OpenAI, Microsoft, Apple, Amazon, Netflix, Tesla, Stripe, Airbnb
- **Minimum Experience**: 4+ years total experience

#### Compensation Requirements (Both must be met):
- **Rate Cap**: ≤ $100/hour
- **Availability**: ≥ 20 hours/week

#### Location Requirements:
- **Approved Regions**: US, USA, Canada, UK, Germany, India (case-insensitive matching)

**Key Functions**:
```python
def evaluate_candidate(self, applicant_id):
    # Returns (is_shortlisted: bool, reason: str)
    # Updates Shortlist Status field
    # Creates record in Shortlisted Leads if approved
```

**Customizing Criteria**:
```python
# Modify tier-1 companies
self.tier1_companies = {
    'Google', 'Meta', 'Your-Company-Here'
}

# Update approved locations
self.approved_locations = {
    'US', 'Canada', 'Remote-OK'
}

# Adjust compensation limits in check_compensation()
rate_ok = preferred_rate <= 120  # Increase rate cap
availability_ok = availability >= 30  # Require more hours
```

### 4. LLM Evaluation (`llm_evaluation.py`)

**Purpose**: AI-powered candidate analysis using Google's Gemini API for consistent, objective evaluation.

**Security Configuration**:
```python
# API key stored in environment variable (never hardcoded)
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Using free Gemini model with rate limiting
self.model = genai.GenerativeModel('gemini-1.5-flash')

# Conservative generation settings
generation_config=genai.types.GenerationConfig(
    max_output_tokens=500,
    temperature=0.3,  # Low temperature for consistent results
)
```

**LLM Prompt Template**:
```python
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
```

**Error Handling & Rate Limiting**:
- **Retry Logic**: 3 attempts with exponential backoff (2^attempt seconds)
- **Duplicate Prevention**: Skips candidates already processed
- **Response Parsing**: Robust regex-based extraction of structured output

### 5. Master Controller (`master_script.py`)

**Purpose**: Orchestrates the entire pipeline for single or batch processing.

**Processing Pipeline**:
1. **Data Compression**: Consolidate applicant data
2. **Shortlist Evaluation**: Apply business criteria
3. **LLM Analysis**: Generate AI insights

**Usage Examples**:
```python
processor = ApplicationProcessor()

# Process single applicant
processor.process_applicant("APP001")

# Process all unprocessed applicants
processor.process_all_applicants()
```

**Batch Processing Logic**:
- Identifies applicants with Applicant ID but no Compressed JSON
- Processes each candidate through full pipeline
- Provides detailed console output for monitoring

## Setup Instructions

### 1. Airtable Configuration
1. Create a new Airtable base
2. Set up the 5 required tables with exact field names as specified
3. Generate API key from Airtable Account settings
4. Copy your Base ID from the URL

### 2. Google Gemini Setup
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Note: Gemini 1.5 Flash has generous free tier limits

### 3. Environment Setup
1. Clone/download the script files
2. Install required packages: `pip install pyairtable python-dotenv google-generativeai`
3. Create `.env` file with your API credentials
4. Test connection: `python compress_data.py`

### 4. Data Import
- Import your applicant data into the normalized tables
- Ensure each applicant has a unique Applicant ID
- Run compression to generate JSON data

## Customization Guide

### Modifying Shortlist Criteria

#### Adding New Experience Criteria
```python
def check_experience(self, experience_list):
    # Add startup experience bonus
    for exp in experience_list:
        company = exp.get('company', '').strip()
        if 'startup' in company.lower() or 'YC' in company:
            return True, f"Startup experience at: {company}"
    
    # Add technology-specific requirements
    required_tech = ['Python', 'React', 'AWS']
    for exp in experience_list:
        tech = exp.get('technologies', '').lower()
        if any(t.lower() in tech for t in required_tech):
            return True, f"Has required technology: {tech}"
```

#### Custom Compensation Logic
```python
def check_compensation(self, salary_data):
    preferred_rate = salary_data.get('preferred_rate', 0)
    currency = salary_data.get('currency', 'USD')
    
    # Different rates by currency
    rate_limits = {
        'USD': 100,
        'EUR': 85,
        'GBP': 80
    }
    
    max_rate = rate_limits.get(currency, 100)
    rate_ok = preferred_rate <= max_rate
    
    # Weekend availability bonus
    if 'weekend' in str(salary_data).lower():
        return True, "Weekend availability bonus"
```


## Security Best Practices

1. **API Keys**: Store in environment variables, never commit to version control
2. **Data Privacy**: Ensure compliance with data protection regulations
3. **Access Control**: Use Airtable's sharing settings to limit base access
4. **Audit Logging**: Track all candidate evaluations and changes
5. **Data Retention**: Implement policies for candidate data lifecycle

## Troubleshooting

### Common Issues

#### "Applicant not found" Error
- Verify Applicant ID format consistency
- Check for leading/trailing spaces in IDs
- Ensure records exist in all required tables

#### LLM Evaluation Failures
- Check Google API key validity and quota
- Verify JSON data is properly formatted
- Monitor for rate limiting (429 errors)

#### Missing Compressed JSON
- Run compression script first: `python compress_data.py`
- Check that linked records exist in all tables
- Verify Applicant ID matching across tables

### Performance Optimization
- Process candidates in smaller batches (10-20 at a time)
- Implement caching for repeated LLM evaluations
- Use Airtable's bulk operations for large datasets
- Consider running during off-peak hours for API limits
