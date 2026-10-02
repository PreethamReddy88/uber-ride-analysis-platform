# 🚗 Uber Ride Analysis Platform

A clean, interactive **Streamlit dashboard** for analysing Uber ride data.  
Built as a beginner-friendly Data Science portfolio project.

---

## 📁 Project Structure

```
uber-ride-analysis/
│
├── data/
│   └── uber_rides.csv        # Raw Uber rides dataset (10 000 rides)
│
├── app.py                    # Main Streamlit dashboard application
├── requirements.txt          # Python dependencies
└── README.md                 # You are here
```

---

## 🚀 Quick Start

### 1. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the dashboard

```bash
streamlit run app.py
```

The app will open automatically in your browser at **http://localhost:8501**.

---

## 📊 Features

| Feature | Description |
|---|---|
| **KPI Cards** | Total Rides · Total Revenue · Avg Fare · Avg Distance · Avg Duration |
| **Sidebar Filters** | Date range · Pickup Location · Dropoff Location · Payment Type |
| **10 Visualisations** | Rides by hour/day/month, top locations, fare & distance distributions, avg fare analysis, payment breakdown |
| **Key Insights** | Auto-generated business insights from the data |

---

## 🛠 Tech Stack

- **Python 3.10+**
- **Pandas** – data manipulation
- **NumPy** – numerical operations
- **Plotly** – interactive charts
- **Matplotlib / Seaborn** – static chart fallback
- **Streamlit** – web dashboard framework

---

## 📈 Dataset Columns

| Column | Description |
|---|---|
| `Ride_ID` | Unique ride identifier |
| `Date` | Trip date |
| `Time` | Trip start time |
| `Pickup_Location` | Where the passenger was picked up |
| `Dropoff_Location` | Where the passenger was dropped off |
| `Distance_KM` | Trip distance in kilometres |
| `Trip_Duration_Min` | Trip duration in minutes |
| `Fare_INR` | Fare amount in INR |
| `Payment_Type` | Cash / Credit Card / Debit Card / UPI |
| `Ride_Status` | Completed / Cancelled |
| `Driver_Rating` | Driver rating (1–5) |
| `Customer_Rating` | Customer rating (1–5) |

---

## 📝 License

This project is for educational and portfolio purposes.
