# Quick Start Guide

## ✅ Dependencies Fixed!

The numpy/pyarrow compatibility issues have been resolved.

## 🚀 Running the Application

### Option 1: Using the startup script (Recommended)
```bash
./run.sh
```

### Option 2: Manual activation
```bash
source venv/bin/activate
streamlit run streamlit_app.py
```

### Option 3: Direct command (from within venv)
```bash
# Make sure you're in the venv (you should see (venv) in your prompt)
streamlit run streamlit_app.py
```

## ⚙️ Before Running

**IMPORTANT**: Make sure you've added your Google Gemini API key to `.env`:

```bash
# Edit .env file
nano .env

# Add this line:
GOOGLE_API_KEY=your_actual_api_key_here
```

## 📊 Testing the App

Once the app opens in your browser:

### Section 1: Single CSV Analysis
1. Upload a CSV from `Sales Dataset/` folder
2. Try the three buttons:
   - **Summarize**: Get AI insights
   - **Ask**: Query the data (e.g., "What is the total sales?")
   - **Save to KB**: Persist to Knowledge Base

### Section 2: Knowledge Base Q&A
1. After saving CSVs to KB in Section 1
2. Ask questions across multiple tables
3. Example: "Which region had the highest sales?"

## 🐛 Troubleshooting

### If you see "No module named 'streamlit'"
Make sure you're in the virtual environment:
```bash
source venv/bin/activate
```

### If you see import errors
The dependencies should now be compatible. If issues persist:
```bash
pip install --upgrade streamlit pandas pyarrow
```

### If Streamlit doesn't open browser
Manually open: `http://localhost:8501`

## 📝 What Was Fixed

- ✅ Updated `google-generativeai` from 0.4.0 to 0.4.1
- ✅ Fixed numpy/pyarrow compatibility (pandas<3, pyarrow<22)
- ✅ All dependencies now compatible with Streamlit

## 🎯 Next Steps

1. Run the app using one of the methods above
2. Add your API key to `.env`
3. Test with the sample data
4. Enjoy your Retail Insights Assistant!
