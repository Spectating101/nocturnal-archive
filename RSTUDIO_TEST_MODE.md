# 🔬 RStudio/Code Execution Test Mode

## Enable Code Execution (Dev Mode)

**Production mode (current)**: No code execution (backend-only)  
**Dev mode (needed for R/Python)**: Full code execution with local LLM

### Setup:

```bash
cd ~/Downloads/llm_automation/project_portfolio/Cite-Agent

# Run the dev setup script
bash dev_setup.sh

# OR manually set in .env.local:
echo "CITE_AGENT_DEV_MODE=true" >> ~/.nocturnal_archive/.env.local
echo "USE_LOCAL_KEYS=true" >> ~/.nocturnal_archive/.env.local

# Add your Cerebras key (for local LLM)
echo "CEREBRAS_API_KEY=csk-34cp53294pcmrexym8h2r4x5cyy2npnrd344928yhf2hpctj" >> ~/.nocturnal_archive/.env.local
```

### Test Code Execution:

```bash
# Test R execution
cite-agent "Run this R code: mean(c(1,2,3,4,5))"
# Should execute and return: 3

# Test with your cm522 data
cd ~/Downloads/cm522-main
cite-agent "Load Annual_Company_Betas.csv and show me summary statistics"

# Test regression
cite-agent "Run the working_betas.R script and show me the results"
```

---

## 🧪 **Test Your R Scripts:**

Available scripts in `~/Downloads/cm522-main/`:
- `working_betas.R` - Beta calculations
- `simple_double_check.R` - Validation
- `calculate_annual_betas.R` - Annual beta analysis
- `fixed_main_regression.R` - Main regression
- `size_effect_problems_summary.R` - Size effect analysis

**Data files:**
- `Annual_Company_Betas.csv` - Annual beta data
- `Test_Monthly_Betas.csv` - Monthly betas
- `All_Company_Betas.csv` - Complete beta dataset

---

## ⚠️ **Important:**

**Production mode** (backend): 
- ✅ Archive API (papers)
- ✅ FinSight API (SEC data)
- ❌ Code execution (disabled)

**Dev mode** (local): 
- ✅ Archive API
- ✅ FinSight API  
- ✅ **Code execution** (R/Python/SQL)

**You can't have both secure monetization AND code execution on the same backend.**

---

## 🎯 **Recommendation:**

**For RStudio testing:**
1. Use dev mode (local keys)
2. Test code execution thoroughly
3. Once satisfied, users choose:
   - **Researchers**: Production mode (no code, but secure/monetized)
   - **Data scientists**: Dev mode (code execution with own keys)

Or build a **sandbox backend** that executes code securely (complex, needs Docker containers).


