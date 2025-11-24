# 🐛 Troubleshooting Guide

## Common Issues and Solutions

### 1. Import Errors - Missing Dependencies

**Error:**
```
ImportError: No module named 'openai'
ModuleNotFoundError: No module named 'langchain'
```

**Solution:**
```powershell
# Activate virtual environment
.\venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# If issues persist, upgrade pip
python -m pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

### 2. API Key Not Found

**Error:**
```
❌ Error: OPENAI_API_KEY not configured
```

**Solution:**
1. Create `.env` file in project root
2. Add your API key:
   ```env
   OPENAI_API_KEY=sk-...your-key-here...
   ```
3. Verify file exists:
   ```powershell
   Get-Content .env
   ```

### 3. Playwright Installation Issues

**Error:**
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**Solution:**
```powershell
# Install Playwright browsers
playwright install chromium

# Or force reinstall
playwright install chromium --force

# Check if installed
playwright --version
```

### 4. Search Results Empty

**Issue:** No search results returned

**Solutions:**

**Option 1:** Use DuckDuckGo (no API key needed)
- Already configured by default
- Check internet connection

**Option 2:** Add SerpAPI key
```env
SERPAPI_KEY=your_serpapi_key_here
```

**Option 3:** Check firewall/proxy settings
```powershell
# Test connectivity
Invoke-WebRequest -Uri "https://duckduckgo.com"
```

### 5. PDF Generation Fails

**Error:**
```
OSError: cannot find font file
```

**Solution:**
```powershell
# Reinstall ReportLab
pip uninstall reportlab
pip install reportlab --no-cache-dir

# Or use DOCX/Markdown instead
python cli.py --query "your topic" --format markdown
```

### 6. Timeout Errors

**Error:**
```
TimeoutError: Page.goto: Timeout 30000ms exceeded
```

**Solution:**

Edit `config.py`:
```python
TIMEOUT_SECONDS = 60  # Increase from 30
```

Or modify specific scraping call:
```python
# In utils/scraper.py
timeout = 90  # Increase timeout
```

### 7. Memory Issues with Large Reports

**Error:**
```
MemoryError: Unable to allocate array
```

**Solutions:**

1. Reduce max results:
   ```python
   # In config.py
   MAX_SEARCH_RESULTS = 5  # Reduce from 10
   ```

2. Limit iterations:
   ```powershell
   python cli.py --query "topic" --iterations 1
   ```

3. Process fewer URLs:
   - Edit `orchestrator/workflow.py`
   - Reduce `max_urls` parameter

### 8. LLM Rate Limits

**Error:**
```
RateLimitError: Rate limit exceeded
```

**Solutions:**

1. Add delays between requests:
   ```python
   # In agents/base_agent.py
   import time
   time.sleep(1)  # Add 1 second delay
   ```

2. Use different model:
   ```env
   OPENAI_MODEL=gpt-3.5-turbo  # Faster, cheaper
   ```

3. Check OpenAI account limits

### 9. JSON Parsing Errors

**Error:**
```
json.JSONDecodeError: Expecting value
```

**Solution:**
- This is handled automatically by fallback parsers
- If persistent, check LLM responses in logs
- Reduce temperature in agent configs

### 10. Database Lock Errors

**Error:**
```
sqlite3.OperationalError: database is locked
```

**Solution:**
```python
# Close other connections
# Or delete database file to reset:
```

```powershell
Remove-Item "database\research_history.db"
```

### 11. Character Encoding Issues

**Error:**
```
UnicodeDecodeError: 'charmap' codec can't decode
```

**Solution:**
- Already handled with `encoding='utf-8'` in code
- If issues persist, check input file encodings

### 12. Permission Errors

**Error:**
```
PermissionError: [WinError 5] Access is denied
```

**Solution:**
```powershell
# Run PowerShell as Administrator
# Or change output directory:
```

Edit `config.py`:
```python
OUTPUT_DIR = Path.home() / "Documents" / "Research"
```

## Debugging Tips

### Enable Verbose Logging

```powershell
python cli.py --query "topic" --verbose
```

### Check Log Files

```powershell
Get-Content "logs\research_agent.log" -Tail 50
```

### Test Components Individually

```powershell
# Test search
python -c "import asyncio; from utils.search import search_web; print(asyncio.run(search_web('test')))"

# Test LLM connection
python -c "from openai import OpenAI; client = OpenAI(); print('Connected')"
```

### Verify Dependencies

```powershell
pip list | Select-String "openai|langchain|playwright"
```

## Getting Help

If issues persist:

1. **Check logs** in `logs/research_agent.log`
2. **Enable verbose mode** with `--verbose` flag
3. **Test internet connection** and API access
4. **Verify API keys** are valid and have credits
5. **Check Python version**: `python --version` (need 3.9+)

## Environment Reset

If all else fails, reset the environment:

```powershell
# Deactivate and remove venv
deactivate
Remove-Item -Recurse -Force venv

# Recreate
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Test
python main.py
```
