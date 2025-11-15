# RedBus Bus Reviews Scraper & Streamlit Analysis

## 1. Project Overview
- **Objective**: Scrape RedBus for bus/operator metadata, user ratings, and textual reviews; persist the dataset in a relational database; surface insights via a Streamlit dashboard so travelers and operators can analyze service quality.
- **Business Use Cases**:
  - Customer insights when comparing different bus services.
  - Sentiment analysis to surface top-rated buses and recurring issues.
  - Service improvement for operators through focused feedback loops.
  - Future recommendation engine driven by user preferences and history.
- **Skill Takeaways**: Selenium automation, BeautifulSoup parsing, Python ETL, data cleaning, sentiment scoring, SQL schema design, Streamlit front-end, optional API integration, deployment + documentation best practices.

## 2. Problem Statement & Approach
- **Problem**: RedBus lacks an open dataset despite holding high-value customer sentiment. Travelers have difficulty making informed choices, and operators lack structured insights that highlight strengths/weaknesses.
- **Solution Strategy**:
  1. **Web Scraping** – Selenium + BeautifulSoup to extract live bus listings, operator info, ratings, and customer reviews.
  2. **Data Cleaning & Transformation** – Text normalization, deduplication, missing-value handling, and NLP-driven sentiment scoring.
  3. **Database Integration** – Persist curated data into SQLite with scalable schema.
  4. **Streamlit Analytics App** – Search, filter, visualize insights, and expose summaries for decision-making.
  5. **Testing & Validation** – Automated checks to ensure scraping accuracy, DB integrity, and UI stability.

## 3. System Architecture
```
            ┌──────────────┐
            │  Selenium    │
            │  Scraper     │
            └──────┬───────┘
                   │ raw HTML
            ┌──────▼────────┐
            │ BeautifulSoup │
            │ + Parsers     │
            └──────┬────────┘
                   │ structured dicts
            ┌──────▼────────┐
            │ Cleaning &    │
            │ NLP (pandas)  │
            └──────┬────────┘
                   │ curated tables
            ┌──────▼────────┐
            │ SQLite        │
            │
            └──────┬────────┘
                   │ SQL queries
            ┌──────▼────────┐
            │ Streamlit UI  │
            │ + Visuals     │
            └───────────────┘
```

## 4. Data Set & Coverage
| Column | Description |
| --- | --- |
| `bus_id` | Hash/UUID derived from operator + route + departure timestamp. |
| `operator_name` | Operator/brand shown on RedBus. |
| `bus_name` | Service name (e.g., “KPN Travels A/C Sleeper”). |
| `bus_type` | Sleeper, Seater, AC/Non-AC, Volvo, etc. |
| `route` | Origin → Destination descriptor with boarding points. |
| `rating` | Float (0–5) scraped from RedBus UI. |
| `rating_count` | Number of reviewers. |
| `review_title` | Optional headline when present. |
| `review_text` | Body of the customer feedback. |
| `review_date` | Parsed `YYYY-MM-DD`. |
| `sentiment` | Derived label (positive/neutral/negative). |
| `created_at` | ETL ingestion timestamp. |

## 5. Data Set Explanation
- **Collection Frequency**: Configurable (daily/weekly); each run tags data with `created_at`.
- **Storage Format**: Raw HTML snapshots (for auditing) + normalized tables in SQLite/PostgreSQL. Intermediate CSV/Parquet optional.
- **Access Pattern**: Streamlit reads via SQLAlchemy; optional REST API for external clients.

## 6. Web Scraping Strategy
- **Tools**: Selenium WebDriver (Chrome/Firefox) for dynamic content, optional BeautifulSoup for post-processing.
- **Steps**:
  1. Launch driver with anti-bot safe delays, load RedBus route listing.
  2. Scroll/paginate to capture all buses; store snapshot metadata.
  3. Click rating widgets to reveal review modals; scrape text, rating, date.
  4. Persist interim JSON/CSV for checkpointing.
  5. Respect robots.txt, add exponential backoff, user-agent rotation, and caching.
- **Error Handling**: Wrap element queries in retries, capture screenshots on failure, log missing fields, skip duplicates.

## 7. Data Cleaning & Transformation
- Drop duplicate reviews via `(bus_id, review_text, review_date)` composite key.
- Normalize casing, trim whitespace, remove emojis unless needed for sentiment.
- Convert ratings to floats; coerce missing fields to `None`.
- Tokenize reviews, remove stopwords, perform stemming/lemmatization for sentiment model (e.g., VADER/TextBlob/custom ML).
- Create derived metrics: `avg_rating`, `rating_std_dev`, `review_length`, `sentiment_score`.
- Store data in tidy tables for analytics and Streamlit filtering.

### Preprocessing Checklist
- Remove duplicates (bus_id + review_text + review_date).
- Clean text (HTML entities, punctuation normalization).
- Handle missing ratings/dates (impute or flag).
- Encode bus types into consistent taxonomy.
- Split route strings into origin/destination columns for filtering.

## 8. Database Design
- Schema fits SQLite.
- Tables:
  - `buses(bus_id PRIMARY KEY, operator_name, bus_name, bus_type, route, avg_rating, rating_count, last_scraped_at)`
  - `reviews(review_id PRIMARY KEY, bus_id FK, rating, review_title, review_text, review_date, sentiment_label, sentiment_score)`
- Use SQLAlchemy for ORM + migrations.
- Indexes on `bus_id`, `operator_name`, `route`, `sentiment_label` for fast queries.

## 9. Streamlit Application
- **Features**:
  - Search by route/operator keyword.
  - Filters for rating range, sentiment, bus type, date range.
  - Visualizations: rating histograms, sentiment pie/bar charts, top-reviewed buses table, word clouds.
  - Review explorer with pagination and highlight of common concerns.
- **UX**: Responsive layout with sidebar filters, main content sections for KPIs, visuals, and raw reviews.
- **State Management**: Caching (`st.cache_data`) for DB calls, session state for filter persistence.

## 10. Installation & Setup
1. **Prerequisites**: Python 3.10+, pip/conda, ChromeDriver/GeckoDriver, Git, make (optional).
2. **Clone & Env**:
   ```bash
   git clone https://github.com/gomathiraja1989/RedBus-Bus-Reviews
   cd RedBus-Bus-Reviews
   pip install -r requirements.txt
   ```
3. **Environment Variables** (`.env`):
   ```
   DATABASE_URL=sqlite:///data/redbus.db
   STREAMLIT_ENV=dev
   SCRAPER_HEADLESS=true
   LOG_LEVEL=INFO
   ```
4. **Drivers**: Download matching ChromeDriver/GeckoDriver, place in `drivers/` or system PATH.

## 11. Running the Pipeline
- **Scraper**:
  ```bash
  python src/scraper/run_scraper.py --route "Chennai,Bangalore" --days 7 --headless
  ```
- **ETL & Sentiment**:
  ```bash
  python src/etl/process_reviews.py --input data/raw/ --output data/curated/
  ```
- **Database Load**:
  ```bash
  python src/db/load.py --db sqlite:///data/redbus.db --data data/curated/
  ```
- **Streamlit App**:
  ```bash
  streamlit run app.py
  ```

## 12. Results & Insights
- Curated database containing bus metadata + review corpus.
- Streamlit portal highlighting:
  - Top-rated buses/operators.
  - Common customer concerns (word clouds/topics).
  - Sentiment timelines per route.
- Downloadable CSV/Excel extracts for business teams.
- Foundation for recommendation, alerting, and API integrations.

## 13. Testing & Validation
- **Unit Tests**: pytest suites for parsers, transformers, DB helpers.
- **Integration**: Mock RedBus HTML to validate end-to-end ETL.
- **UI Testing**: Streamlit `st.session_state` snapshots + manual regression.

- **Data Quality Checks**: Null ratio thresholds, rating bounds, sentiment distribution sanity.
