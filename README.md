## Features

* **Automated CV Evaluation**: Scores and provides reasons for each CV suitability based on a job description using the Gemini-2.5-flash model.
* **Multiple File Support**: Processes CVs in PDF, PNG, JPG, and JPEG formats.
* **Batch Processing**: Handles multiple CVs concurrently with configurable batch sizes and delays to manage API rate limits.
* **Detailed Output**: Generates a JSON file with `participant_id`, `score`, and `reasons` for each evaluated CV.
* **Token Usage Tracking**: Records and outputs token usage for each API call, helping monitor costs.

---
## Setup

To run this tool, follow these steps:

1.  **Clone the Repository (or download the code):**
    ```bash
    git clone git@github.com:Cv-Vision/AI_POCS.git
    cd AI_POCS
    ```

2.  **Install Dependencies:**
    Make sure you have `pip` installed. Then, install the required Python packages from `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set Up Your Gemini API Key:**
    Create a **`.env`** file in the root directory of your project (the same directory as the script) and add your Google Gemini API key in the following format:
    ```
    GEMINI_API_KEY=YOUR_API_KEY_HERE
    ```
    Replace `YOUR_API_KEY_HERE` with your actual Gemini API key.

---
## Usage

1.  **Place Your CVs**:
    Create a folder named **`cvs`** in the same directory as the script. Place all the CVs (in PDF, PNG, JPG, or JPEG format) you want to validate into this `cvs` directory.

2.  **Provide the Job Description**:
    Place your job description as a PDF file named **`job_description.pdf`** in the same root directory as the script.

3.  **Prepare Output Files (Optional but Recommended)**:
    Before running the script, it's recommended to clear the contents of **`output-gemini-images.json`** and **`token-usage.json`** from previous runs. This ensures you have fresh results.

    Alternatively, if you want to keep previous results, you can modify the `output_json_file` and `token_usage_file` variables directly in the script to use different filenames for each run.

4.  **Run the Script**:
    Execute the Python script from your terminal:
    ```bash
    python poc_gemini_images.py
    ```
    (Replace `your_script_name.py` with the actual name of your Python script file.)

---
## Output

The script will generate two JSON files in the root directory:

* **`output-gemini-images.json`**: This file will contain an array of JSON objects, each representing an evaluated CV with its `participant_id`, `score` (0-100), and `reasons` for the given score.

    Example:
    ```json
    [
      {
        "participant_id": "...",
        "score": 85,
        "reasons": [
          "Strong experience in relevant industry.",
          "Good match for required seniority level.",
          "Demonstrates basic English proficiency."
        ]
      },
      {
        "participant_id": "...",
        "score": 40,
        "reasons": [
          "Lacks experience in the specified industry.",
          "Seniority level does not match job requirements.",
          "English proficiency is not clearly demonstrated."
        ]
      }
    ]
    ```

* **`token-usage.json`**: This file will log the token usage for each API call, breaking down prompt tokens, response tokens, and total tokens.

    Example:
    ```json
    [
      {
        "participant_id": "...",
        "prompt_tokens": 1500,
        "prompt_tokens_local": 200,
        "prompt_tokens_image": 1300,
        "response_tokens": 50,
        "total_tokens": 1550
      }
    ]
    ```