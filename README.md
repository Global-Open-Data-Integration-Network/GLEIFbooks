# GLEIFbooks
This repository contains a collection of Jupyter notebooks demonstrating practical use cases of LEI (Legal Entity Identifier) data. Each notebook focuses on a specific topic and provides example code to help data users explore, analyze, and apply LEI data effectively.

All notebooks are maintained and published by the **[Global Legal Entity Identifier Foundation (GLEIF)](https://www.gleif.org)**.

## Getting Started

### Installation

#### Option 1: Using pip (Recommended)

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### Option 2: Using conda

1. Create a new conda environment:
   ```bash
   conda create -n gleif-mapping python=3.9
   conda activate gleif-mapping
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

#### Option 3: Google Colab

1. Upload the entire project folder to Google Drive
2. Open the notebook in Google Colab
3. Run the first cell and adjust the sys.path, if necessary

## Usage

### Local Environment

1. Start Jupyter Notebook:
   ```bash
   jupyter notebook
   ```

2. Open the ipynb file

3. Run the cells in order

## Configuration

The notebooks support flexible configuration through flags in the second cell:

### Data Scope Options
- `USE_FULL_DATASET = True`: Download and use all available columns
- `USE_FULL_DATASET = False`: Use only essential columns (faster, less memory)

### Storage Options
- `SAVE_TO_DISK = True`: Save files to disk
- `SAVE_TO_DISK = False`: Keep data in memory only

### Example Configurations

```python
# Quick analysis with minimal resources
USE_FULL_DATASET = False
SAVE_TO_DISK = False

# Comprehensive analysis with persistence
USE_FULL_DATASET = True
SAVE_TO_DISK = True

# Balanced approach
USE_FULL_DATASET = False
SAVE_TO_DISK = True
```

## Project Structure

```
jupyter-gleifbooks/
├── 2025-08-18_MappingExercise_v1.0.ipynb  # Mapping notebook
├── requirements.txt                        # Python dependencies
├── README.md                              # This documentation file
├── LICENSE.md                             # License information
├── .gitignore                             # Git ignore patterns
├── utils/                                 # Utility modules package
│   ├── __init__.py                       # Package initialization and environment setup
│   ├── download_utils.py                 # GLEIF Golden Copy download utilities
│   ├── gleif_api_utils.py                # GLEIF JSON:API client
│   ├── visualization_utils.py            # Data visualization utilities
│   └── codelist_utils.py                 # Registration Authority code list utilities
├── cache/                                 # Cached data files (auto-created)
├── gc_downloads/                          # Golden Copy downloads (if SAVE_TO_DISK=True)
├── downloads/                             # Mapping file downloads (if SAVE_TO_DISK=True)
└── lib/ 
```

## Dependencies

### Core Dependencies
- **pandas** (≥1.5.0): Data manipulation and analysis
- **numpy** (≥1.21.0): Numerical computing
- **requests** (≥2.28.0): HTTP library for web requests
- **beautifulsoup4** (≥4.11.0): HTML parsing for web scraping
- **matplotlib** (≥3.5.0): Data visualization

### Optional Dependencies
- **jupyter**: Jupyter notebook support (for local development)
- **google-colab**: Google Colab integration (automatic in Colab)

## Troubleshooting

### Common Issues

1. **Import Errors in Google Colab**:
   - Make sure to upload the entire project folder to Google Drive
   - Run the first cell to set up the environment
   - Ensure that the `utils` folder is included in your upload

2. **Memory Issues with Large Datasets**:
   - Set `USE_FULL_DATASET = False` to use only essential columns
   - Set `SAVE_TO_DISK = True` to avoid keeping large datasets in memory
   - Use the time-based download feature to get smaller datasets

3. **Time-based Download Issues**:
   - The Golden Copy is published three times a day (UTC): 00:00, 08:00, 16:00. If a Golden Copy file is not available, please choose an earlier publication

### Getting Help

If you encounter issues:
1. Check that all dependencies are installed correctly
2. Verify your internet connection
3. Try different configuration options (memory vs disk, full vs subset)
4. Check the GLEIF website for any service outages
5. Contact dataqualityfeedback@gleif.org

## License

CC0 1.0 Universal – No rights reserved.  
See the [LICENSE](LICENSE.md) file or <https://creativecommons.org/publicdomain/zero/1.0/>.
