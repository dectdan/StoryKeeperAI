# 📝 StoryKeeper AI

[![Tests](https://github.com/dectdan/StoryKeeperAI/actions/workflows/tests.yml/badge.svg)](https://github.com/dectdan/StoryKeeperAI/actions)

StoryKeeper AI is a desktop application built with **Python** and **PyQt6** for managing story dictionaries, contexts, and spelling/grammar checks.  
It supports:
- 📚 Multi-meaning word dictionary with categories and contexts  
- 🧠 Modular “brains” for different worlds  
- ✅ Built-in spell checking and future grammar checking  
- 💾 Project export/import with dictionary and contexts  
- 🧪 Full test coverage with **pytest** and **pytest-qt**

---

## 🚀 Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/dectdan/StoryKeeperAI.git
   cd StoryKeeperAI

py -3.11 -m venv venv
venv\Scripts\activate


pip install --upgrade pip
pip install -r requirements.txt

python app.py

pytest -v

