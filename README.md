# 🎬 IMDb Movie Data Project

This project automates the process of scraping IMDb data, cleaning it, storing it in MySQL, and visualizing it in a Python dashboard.

## 📂 Project Files

- **csv_loader.py** → Reads raw IMDb data and processes it into a clean CSV.
- **imdb_dashboard.py** → Builds a dashboard with charts/visualizations of movie data.
- **import.py** → Helper script for data import utilities.
- **load_to_mysql.py** → Loads processed CSV data into a MySQL database.
- **outcsv/** → Stores scraped/exported CSV data.

## 🚀 Workflow

1. **Data Extraction**  
   Run `csv_loader.py` to generate/export IMDb data into `outcsv/outcsv.csv`.

2. **Data Cleaning & Preparation**  
   Scripts clean votes, ratings, runtime, and ensure proper formatting.

3. **Data Loading**  
   Run `load_to_mysql.py` to insert data into MySQL (with SQLAlchemy + pandas).

4. **Visualization**  
   Run `imdb_dashboard.py` to generate an interactive dashboard of movie ratings, genres, votes, etc.

---

## ⚙️ Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/<your-username>/imdb-project.git
cd imdb-project
pip install -r requirements.txt
