# 4chan Toxicity Analysis Project

## Overview
This project analyzes toxicity patterns on 4chan's `/pol/` board by comparing two content moderation APIs: OpenAI's Moderation API and Google's Perspective API. The analysis provides insights into automated content moderation systems while assessing technical and analytical skills.

## Project Structure
```
4chan-toxicity-analysis/
├── data/                    # Raw collected data from 4chan
├── processed_data/          # Cleaned and processed data
├── src/                     # Source code
│   ├── data_collection/     # 4chan data collection scripts
│   ├── api_integration/     # API integration scripts
│   └── analysis/           # Analysis and visualization scripts
├── results/                # Analysis results and visualizations
├── reports/                # Research report files
├── config/                 # Configuration files
├── tests/                  # Test files
├── .env                    # API keys (not in repository)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Setup Instructions

### 1. Prerequisites
- Python 3.8 or higher
- Git
- OpenAI API account (free tier)
- Google Cloud account with Perspective API enabled (free tier)

### 2. Installation
```bash
# Clone the repository
git clone <your-repo-url>
cd 4chan-toxicity-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
1. Create a `.env` file in the project root
2. Add your API keys:
```
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_credentials.json
```

### 4. Test API Connectivity
```bash
python src/api_test.py
```

## Project Phases

### Phase 1: Project Setup ✅
- [x] Environment setup
- [x] API account creation
- [x] Project structure
- [x] Configuration system

### Phase 2: Data Collection
- [ ] 4chan API integration
- [ ] Data collection (5,000-10,000 posts)
- [ ] Rate limiting implementation
- [ ] Error handling

### Phase 3: API Integration
- [ ] OpenAI Moderation API integration
- [ ] Google Perspective API integration
- [ ] Batch processing
- [ ] Data persistence

### Phase 4: Data Analysis
- [ ] Statistical analysis
- [ ] Comparative study
- [ ] Research questions analysis
- [ ] Performance metrics

### Phase 5: Visualization
- [ ] Correlation plots
- [ ] Agreement/disagreement charts
- [ ] Category-wise distributions
- [ ] Performance comparisons

### Phase 6: Research Report
- [ ] LaTeX report setup
- [ ] Methodology documentation
- [ ] Results presentation
- [ ] Discussion and implications

### Phase 7: Final Submission
- [ ] Git repository finalization
- [ ] GitHub repository setup
- [ ] Deliverable preparation

## Research Questions
1. How well do the APIs agree on toxicity detection?
2. What content types show highest disagreement?
3. Which API demonstrates greater sensitivity to different toxic content categories?
4. What patterns emerge in false positive/negative classifications?

## Technical Requirements
- **Data Volume**: 5,000-10,000 posts from 4chan `/pol/` board
- **Rate Limiting**: Minimum 1 request per second
- **APIs**: OpenAI Moderation API, Google Perspective API
- **Analysis**: Statistical comparison, correlation analysis, visualization
- **Documentation**: Comprehensive research report in PDF format

## Deliverables
1. **Git Repository**: Complete source code, data, and documentation
2. **Research Report**: PDF with methodology, results, and implications
3. **Visualizations**: Charts and graphs supporting findings
4. **Documentation**: Setup and execution instructions

## Usage
```bash
# Test API connectivity
python src/api_test.py

# Run data collection (Phase 2)
python src/data_collection/collect_4chan_data.py

# Run API integration (Phase 3)
python src/api_integration/process_apis.py

# Run analysis (Phase 4)
python src/analysis/analyze_data.py

# Generate visualizations (Phase 5)
python src/analysis/create_visualizations.py
```

## Contributing
This is a research project for academic assessment. Please ensure:
- All commits are meaningful and descriptive
- API keys are never committed to the repository
- Data collection follows ethical guidelines
- Rate limiting is properly implemented

## License
Academic research project - see project description for details.

## Contact
For questions about this project, refer to the project description document.