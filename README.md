# 🎓 Smart Student Agent — Agentic AI & Chainlit Workspace

An intelligent learning assistant ecosystem engineered using **pure Python logic** and the **Chainlit UI framework**. This application implements customized **Agentic AI** workflows, decision-making forks, and multi-file orchestration to dynamically route and solve student queries within a beautiful conversational interface.

---

## 🚀 Architectural Core & Features

* **Localized Agentic AI Engineering:** Uses algorithmic Python workflows to handle query parsing, state management, and intent routing natively.
* **Built-in Chainlit Interface:** Leverages Chainlit's native streaming and state decorators (`@cl.on_chat_start`, `@cl.on_message`) to provide a reactive user experience.
* **Modular Multi-File Codebase:** Features dedicated scripts like `main.py`, `enhanced_main.py`, `sidebar_manager.py`, and database modules to keep execution scopes clean.
* **Stateful Logging Layer:** Built-in persistence utilizing `chat_history.db` to safely cache user context arrays across system restarts.

---

## 📥 How to Run and Use This Project Locally

Since this application runs on a localized runtime environment, any user can execute and test your agent by following these three straightforward steps:

# Clone the repository and enter the directory
git clone https://github.com/HibaDawood/Smart-Student-Agent.git && cd Smart-Student-Agent

# Install the Chainlit interface framework
pip install chainlit

# Launch the live interactive chat server
chainlit run main.py -w
