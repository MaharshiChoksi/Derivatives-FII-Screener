# Derivatives FII Screener
A Streamlit-based web application for analyzing Futures & Options (F&O) participant open interest data and Foreign Institutional Investor (FII) statistics to generate potential trading signals.

## Features
- **Data Scraping**: Automatically fetches the latest participant OI and FII stats from NSE archives
- **Instrument-wise Analysis**: Provides trading signals (LONG/SHORT) for various derivative instruments including:
  - Index Futures (NIFTY, BANKNIFTY, etc.)
  - Stock Futures
  - Index Options
  - Stock Options
- **Interactive Dashboard**: User-friendly interface with date selection and real-time data visualization
- **Caching**: Efficient data caching to minimize API calls and improve performance
- **Clear Cache Option**: Manual cache clearing for fresh data fetches

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/MaharshiChoksi/Derivatives-FII-Screener.git
   cd Derivatives-FII-Screener
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the Streamlit app:
   ```bash
   streamlit run src/app.py
   ```
2. Open your browser to the provided local URL (usually http://localhost:8501)
3. Select current and previous working dates
4. Click "Start Computing" to analyze the data
5. Review the instrument-wise signals and data tables

## Trading Signals Logic
The app generates signals based on the following conditions:
- **LONG Signal**: Participant OI > Previous Day FII OI AND Current Day FII OI > 0
- **SHORT Signal**: Participant OI < Previous Day FII OI AND Current Day FII OI < 0
- **No Signal**: When the above conditions are not met

## Data Sources
- NSE Participant OI Aftermarket Daily Reports
- NSE FII Stats OI Aftermarket Daily Reports

## Disclaimer
⚠️ **This is educational content only and not investment advice.** Do your own research before trading. Past performance does not guarantee future results. Trading in derivatives involves significant risk and may not be suitable for all investors.

## Contributing
Feel free to submit issues and enhancement requests!

## License
This project is for educational purposes. Please check NSE terms of service for data usage.
