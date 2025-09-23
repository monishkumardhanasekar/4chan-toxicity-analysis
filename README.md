# 4chan Toxicity Analysis Project

## Overview
This project analyzes toxicity patterns on 4chan's `/pol/` board by comparing two content moderation APIs: OpenAI's Moderation API and Google's Perspective API. The analysis provides insights into automated content moderation systems while assessing technical and analytical skills.

## Project Structure
```
4chan-toxicity-analysis/
├── src/                     # Source code
│   ├── data/               # Collected data and logs
│   │   ├── final_collection.json      # 7,362 posts from /pol/ board
│   │   ├── api_results.json           # 6,843 processed API results
│   │   ├── api_progress.json          # API processing progress
│   │   ├── api_processing.log         # API processing logs
│   │   ├── collection_summary.json    # Collection statistics
│   │   └── collection.log             # Collection activity log
│   ├── data_collection/    # Data collection system
│   │   ├── core/           # Core collection logic
│   │   ├── config/         # Configuration management
│   │   └── utils/          # Utility functions
│   ├── api_integration/    # API integration system
│   │   ├── clients/        # OpenAI and Google API clients
│   │   ├── core/           # Batch processing logic
│   │   └── config.py       # API configuration
│   ├── analysis/           # Analysis and visualization scripts (Phase 4-5)
│   └── api_test.py         # API connectivity test
├── reports/                # Analysis outputs and results
│   ├── figures/            # Generated visualizations (11 figures)
│   │   ├── correlation_heatmap.png
│   │   ├── google_distributions.png
│   │   ├── openai_distributions.png
│   │   └── ... (8 more figures)
│   └── metrics/            # Statistical analysis results (10 metrics files)
│       ├── agreement_summary.json
│       ├── correlations_summary.json
│       ├── distributions_summary.json
│       └── ... (7 more metrics files)
├── notebooks/              # Jupyter notebooks for analysis
│   └── phase4_statistical_analysis.ipynb
├── collect_data.py         # Main data collection script
├── process_apis.py         # Main API processing script
├── setup.py               # Project setup script
├── .env                   # API keys (not in repository)
├── requirements.txt       # Python dependencies
├── env_template.txt      # Environment variables template
└── README.md             # This file
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
GOOGLE_PERSPECTIVE_API_KEY=your_google_perspective_api_key_here
```
3. Copy from template: `cp env_template.txt .env`

```

## Project Phases

### Phase 1: Project Setup
- [x] Environment setup
- [x] API account creation
- [x] Project structure
- [x] Configuration system

### Phase 2: Data Collection
- [x] 4chan API integration
- [x] Data collection (5,000-10,000 posts)
- [x] Rate limiting implementation (1.2s between requests) - min 1 seconds
- [x] Error handling and retry logic
- [x] Data validation and quality checks

#### Collection Results
- **Total Posts**: 7,362 posts (98.16% of 7,500 target)
- **Threads Processed**: 99 threads
- **Collection Duration**: 20.6 seconds
- **Geographic Distribution**: 61 countries represented (US: 44.7%, GB: 6.3%, CA: 5.4%)
- **Content Quality**: 153 image-only posts filtered out
- **Data Structure**: Hierarchical JSON with OP posts and replies separated

### Phase 3: API Integration
- [x] OpenAI Moderation API integration
- [x] Google Perspective API integration
- [x] Batch processing system
- [x] Data persistence and resume functionality
- [x] Rate limiting compliance (1 request/second)
- [x] Error handling and retry logic
- [x] Progress tracking and logging

#### API Processing Results
- **Total Posts Processed**: 7,362 posts (100% complete)
- **Successful Posts**: 6,843 posts (93.0% success rate)
- **Failed Posts**: 519 posts (7.0% failure rate)
- **Google API Success**: 6,843 posts
- **OpenAI API Success**: 6,843 posts
- **Processing Time**: 4.3 hours
- **Processing Rate**: 1,715 posts/hour
- **Data Structure**: Complete API results with all categories and scores

### Phase 4: Data Analysis
- [x] Statistical analysis
- [x] Comparative study
- [x] Research questions analysis
- [x] Performance metrics

### Phase 5: Visualization
- [x] Correlation plots
- [x] Agreement/disagreement charts
- [x] Category-wise distributions
- [x] Performance comparisons


## Research Questions
1. How well do the APIs agree on toxicity detection?
2. What content types show highest disagreement?
3. Which API demonstrates greater sensitivity to different toxic content categories?
4. What patterns emerge in false positive/negative classifications?

## Technical Requirements
- **Data Volume**: 7,362 posts from 4chan `/pol/` board 
- **Rate Limiting**: 1 request per second (Google API compliance) 
- **APIs**: OpenAI Moderation API, Google Perspective API 
- **Processing**: 6,843 posts successfully processed (93.0% success rate) 
- **Analysis**: Statistical comparison, correlation analysis, visualization



## Usage

  ### Data Collection (Phase 2)
```bash
# Run full data collection (7,362 posts)
python collect_data.py

# Custom collection parameters
python collect_data.py --target-posts 5000 --rate-limit 1.5

# Validate existing data
python collect_data.py --validate-only
```

### API Integration (Phase 3) 
```bash
# Test API connectivity
python src/api_test.py

# Run full API processing (6,843 successful posts)
python process_apis.py

# Resume processing from specific batch
python process_apis.py --resume-from-batch 20

# Custom batch size and rate limiting
python process_apis.py --batch-size 100 --google-rate-limit 1.0
```

### Analysis (Phase 4)
```bash
# Open the statistical analysis notebook
jupyter notebook notebooks/phase4_statistical_analysis.ipynb

# Or generate metrics via scripts (optional, if you prefer CLI)
python src/analysis/compute_distributions.py
python src/analysis/compute_agreement.py
python src/analysis/compute_sensitivity.py
python src/analysis/compute_disagreements.py
python src/analysis/compute_fp_fn.py
python src/analysis/compute_temporal_length.py
```

## Key Findings

### Research Question Results
1. **API Agreement**: Strong correlation (r=0.83) between Google toxicity and OpenAI harassment scores
2. **Content Disagreement**: Highest disagreement in profanity detection (r=0.43) 
3. **Sensitivity Differences**: Google shows higher sensitivity to identity attacks
4. **False Positives/Negatives**: Clear patterns in length-based classification differences

### Statistical Significance
- Mann-Whitney U tests with FDR correction applied
- Bootstrap confidence intervals for all correlations
- 93% API success rate with comprehensive error handling

## Research Report

A comprehensive PDF research report will be included in the repository, covering:
- Executive Summary
- Detailed Methodology
- Statistical Analysis Results  
- Discussion of Implications
- Limitations and Future Work

<p align="center">
  <a href="reports/Comparative_Analysis_of_Content_Moderation_APIs__A_Study_of_Toxicity_Detection_on_4chan_s__pol__Board_.pdf" target="_blank">
    <img src="https://img.shields.io/badge/📄%20View%20Research%20Report-PDF-red?style=for-the-badge" alt="Research Report PDF">
  </a>
</p>

## Limitations

- **API Failures**: 7% failure rate (519/7,362 posts) due to API timeouts/errors
- **Data Scope**: Limited to /pol/ board, may not generalize to other platforms
- **Temporal Scope**: Single collection period, no longitudinal analysis
- **Content Filtering**: Image-only posts excluded (153 posts)
- **Rate Limiting**: Collection efficiency limited by 1.2s request delays

## Contributing

This project was completed as part of a research assessment for the Yang Lab. For collaboration inquiries or questions about the methodology, please contact the project author.

## License
This project is for academic research purposes. All data collection follows 4chan's terms of service and API guidelines.

## Contact

**Project Author**: Monish Kumar Dhanasekar
**Email**: mdhanasekar@binghamton.edu  
Research Assessment - Yang Lab  

---

*This project demonstrates proficiency in social media data collection, API integration, statistical analysis, and technical reporting as required for research work in computational social science.*
