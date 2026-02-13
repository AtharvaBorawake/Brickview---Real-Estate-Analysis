import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt



# Function to connect to SQLite database
def get_data(query, params=None):
    conn = sqlite3.connect("real_estate_database1.sqlite")
    if params:
        df = pd.read_sql_query(query, conn, params=params)
    else:
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df




# Streamlit App Title
st.set_page_config(page_title="BrickView: Real Estate Analytics Platform")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Project Introduction", "Data Visualization", "SQL insights", "Creator Info"])


# -------------------------------- PAGE 1: Introduction --------------------------------
if page == "Project Introduction":
    st.title("🏢 BrickView")
    st.subheader("Real Estate Analytics & Insights Platform")

    st.image("propertyimage.png")
    
    st.markdown("---")
    st.subheader("📊 Business Use Cases")

    cols = st.columns(3)

    with cols[0]:
        st.image("1.png", caption="Buyer & Investor Insights", width=200)

    with cols[1]:
        st.image("2.png", caption="Agent Performance Tracking", width=200)

    with cols[2]:
        st.image("3.png", caption="Market & Pricing Trends", width=200)

    st.markdown("---")
            
    st.markdown("## 📌 Overview")
    st.write("""
    The real estate market is vast and dynamic, with properties being listed, sold, 
    and evaluated every day. Buyers, sellers, and agents often lack accessible tools 
    to monitor trends, pricing, and sales performance.

    **BrickView** addresses this challenge by providing an interactive analytics 
    dashboard built using **SQL and Streamlit**.
    """)

    st.markdown("## 🎯 Objectives")
    st.markdown("""
    - Analyze property listings, agent performance, and sales patterns  
    - Provide insights into pricing, time on market, and property types  
    - Enable filtering by location, property type, price, and sales agent  
    - Display interactive visuals such as maps and charts for better understanding  
    """)


    st.markdown("## 🛠️ Technologies Used")
    st.markdown("""
    - **Python**
    - **SQL (SQLite)**
    - **Streamlit**
    - **Pandas, Matplotlib, Seaborn**
    """)

    st.info("👉 Use the navigation menu to explore data visualizations, SQL insights, and analysis.")
# -------------------------------- PAGE 2:  Data Visualization --------------------------------

    
elif page == "Data Visualization":
    
    
    st.title("📊 Data Visualization")

    col1, col2 = st.columns(2)
    
    
    cities = get_data("SELECT DISTINCT City FROM listings")["City"].tolist()
    property_types = get_data("SELECT DISTINCT Property_Type FROM listings")["Property_Type"].tolist()
    agents = get_data("SELECT DISTINCT Name FROM agents")["Name"].tolist()

    with col1:
        selected_cities = st.multiselect("City", cities)
        selected_property = st.selectbox("Property Type", ["All"] + property_types)
        selected_agent = st.selectbox("Agent", ["All"] + agents)

    price_df = get_data("SELECT MIN(Price) as min_p, MAX(Price) as max_p FROM listings")
    min_price, max_price = int(price_df.min_p[0]), int(price_df.max_p[0])

    with col2:
        price_range = st.slider("Price Range", min_price, max_price, (min_price, max_price))

        
        # Date Type – Listed or Sold
        date_type = st.selectbox(
            "Filter Date By",
            ["Date Listed", "Date Sold"]
        )

        # Date Range – Date Picker
        date_range = st.date_input(
            "Date Range",
            value=[]
        )
    
    base_query = """
    SELECT
        l.Listing_ID,
        l.City,
        l.Property_Type,
        l.Price,
        l.Date_Listed,
        a.Name AS Agent_Name,
        s.Date_Sold,
        s.Days_on_Market,
        l.Latitude as latitude,
        l.Longitude as longitude
    FROM listings l
    JOIN agents a ON l.Agent_ID = a.Agent_ID
    LEFT JOIN sales s ON l.Listing_ID = s.Listing_ID
    WHERE 1=1
    """

    params = []

    if selected_cities:
        placeholders = ",".join(["?"] * len(selected_cities))
        base_query += f" AND l.City IN ({placeholders})"
        params.extend(selected_cities)

    if selected_property != "All":
        base_query += " AND l.Property_Type = ?"
        params.append(selected_property)

    if selected_agent != "All":
        base_query += " AND a.Name = ?"
        params.append(selected_agent)

    base_query += " AND l.Price BETWEEN ? AND ?"
    params.extend(price_range)

    # Date filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        if date_type == "Date Listed":
            base_query += " AND l.Date_Listed BETWEEN ? AND ?"
        else:
            base_query += " AND s.Date_Sold BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    df = get_data(base_query, params)

    st.subheader("📋 Filtered Listings")
    st.dataframe(df)
    
    st.download_button(
            "⬇️ Download CSV",
            df.to_csv(index=False),
            "Filtered_listings.csv",
            "text/csv"
        )
    
    # ---------------- MAP ---------------- #

    
    st.subheader("🗺️ Interactive Map of Current Property Listings by City")

    map_df = df[
        (df["Date_Sold"].isna()) &
        (df["latitude"].notna()) &
        (df["longitude"].notna())
    ][["latitude", "longitude"]]

    map_df["latitude"] = map_df["latitude"].astype(float)
    map_df["longitude"] = map_df["longitude"].astype(float)

    if not map_df.empty:
        st.map(map_df)
    else:
        st.warning("No active listings available for selected city.")

    # ---------------- BAR CHART ---------------- #

    st.subheader("📊 Average Price by City")
    city_price = df.groupby("City")["Price"].mean().reset_index()
    st.bar_chart(city_price.set_index("City"))

    # ---------------- PIE CHART ---------------- #

    st.subheader("🥧 Property Type Distribution")
    fig1, ax1 = plt.subplots()
    df["Property_Type"].value_counts().plot.pie(
        autopct="%1.1f%%",
        ax=ax1
    )
    ax1.set_ylabel("")
    st.pyplot(fig1)

    # ---------------- LINE CHART ---------------- #

    st.subheader("📈 Monthly Sales Trend")

    sales_df = df.dropna(subset=["Date_Sold"]).copy()

    if not sales_df.empty:
        # Convert to datetime
        sales_df["Date_Sold"] = pd.to_datetime(sales_df["Date_Sold"])

        # Create Month column as datetime (month start)
        sales_df["Month"] = sales_df["Date_Sold"].dt.to_period("M").dt.to_timestamp()

        # Aggregate
        trend = sales_df.groupby("Month").size().reset_index(name="Sales_Count")

        # Plot
        st.line_chart(trend.set_index("Month"))

elif page == "SQL insights":

        st.title(" SQL Insights")
        st.write("Run predefined SQL queries and explore insights from the BrickView database.")

        queries = {
            "1. What is the average listing price by city?": {
                "sql": """
                    select City ,
                    Avg(price) as Avg_Price
                    from listings 
                    group by city
                """,
                "chart": "bar",
                "x": "City",
                "y": "Avg_Price"
            },

            "2. What is the average price per square foot by property type?": {
                "sql": """
                    SELECT Property_Type,
                        ROUND(AVG(Price / Sqft), 2) AS Avg_Price_Per_Sqft
                    FROM listings
                    WHERE Sqft > 0
                    GROUP BY Property_Type
                """,
                "chart": "bar",
                "x": "Property_Type",
                "y": "Avg_Price_Per_Sqft"
            },

            "3. How does furnishing status impact property prices?": {
                "sql": """
                    SELECT
                        p.furnishing_status,
                        COUNT(*) AS total_listings,
                        AVG(l.price) AS avg_price,
                        AVG(l.price / l.sqft) AS avg_price_per_sqft
                    FROM listings l
                    JOIN property_attributes p
                        ON l.listing_id = p.listing_id
                    WHERE l.sqft > 0
                    GROUP BY p.furnishing_status
                    ORDER BY avg_price_per_sqft DESC;
                """,
                "chart": "bar",
                "x": "furnishing_status",
                "y": "avg_price_per_sqft"
        
            },

            "4. Do properties closer to metro stations command higher prices?": {
                "sql": """
                        SELECT
                            CASE
                                WHEN pa.Metro_Distance_Km <= 1 THEN '0–1 km'
                                WHEN pa.Metro_Distance_Km <= 3 THEN '1–3 km'
                                WHEN pa.Metro_Distance_Km <= 5 THEN '3–5 km'
                                ELSE '5+ km'
                            END AS metro_distance_bucket,
                            COUNT(*) AS listings,
                            ROUND(AVG(l.Price), 2) AS avg_price,
                            ROUND(AVG(l.Price * 1.0 / l.sqft), 2) AS avg_price_per_sqft
                        FROM listings l
                        JOIN property_attributes pa
                        ON l.Listing_ID = pa.Listing_ID
                        GROUP BY metro_distance_bucket
                        ORDER BY MIN(pa.Metro_Distance_Km);
                    """,
                     "chart": None,
                    
            },

            "5. Are rented properties priced differently from non-rented ones?": {
                "sql": """
                    SELECT
                        p.is_rented ,
                        COUNT(*) AS total_listings,
                        AVG(l.price) AS avg_price,
                        AVG(l.price / l.sqft) AS avg_price_per_sqft
                    FROM listings l
                    JOIN property_attributes p
                        ON l.listing_id = p.listing_id
                    WHERE l.sqft > 0
                    GROUP BY p.is_rented ;
                """,
                "chart": "bar",
                "x": "is_rented",
                "y": "avg_price"
            },
            "6. How do bedrooms and bathrooms affect pricing?": {
                "sql": """
                        SELECT
                            p.bedrooms ,
                            p.bathrooms,
                            COUNT(*) AS total_listings,
                            AVG(l.price) AS avg_price,
                            AVG(l.price / l.sqft) AS avg_price_per_sqft
                        FROM listings l
                        JOIN property_attributes p
                            ON l.listing_id = p.listing_id
                        WHERE l.sqft > 0
                        GROUP BY p.bedrooms, p.bathrooms 
                        order by p.bedrooms, p.bathrooms;
                """,
                "chart": None
            },
            "7. Do properties with parking and power backup sell at higher prices?": {
                "sql": """
                    SELECT
                        p.parking_available ,
                        p.power_backup,
                        COUNT(*) AS total_listings,
                        ROUND(AVG(l.price),2) AS avg_price,
                        AVG(l.price / l.sqft) AS avg_price_per_sqft
                    FROM listings l
                    JOIN property_attributes p
                        ON l.listing_id = p.listing_id
                    WHERE l.sqft > 0
                    GROUP BY p.parking_available, p.power_backup 
                    order by avg_price_per_sqft desc;
                """,
                "chart": None
            },
            
            "8. How does year built influence listing price?": {
                "sql": """
                    SELECT
                        p.year_built ,
                        COUNT(*) AS total_listings,
                        ROUND(AVG(l.price),2) AS avg_price,
                        AVG(l.price / l.sqft) AS avg_price_per_sqft
                    FROM listings l
                    JOIN property_attributes p
                        ON l.listing_id = p.listing_id
                    WHERE l.sqft > 0
                    GROUP BY p.year_built 
                    order by avg_price_per_sqft desc;
                """,
                "chart": "line",
                "x": "year_built",
                "y": "avg_price"
            },
            "9. Which cities have the highest median property prices?": {
                "sql": """
                    WITH ranked AS (
                        SELECT
                            City,
                            Price,
                            ROW_NUMBER() OVER (PARTITION BY City ORDER BY Price) AS rn,
                            COUNT(*) OVER (PARTITION BY City) AS cnt
                        FROM listings
                    )
                    SELECT
                        City,
                        ROUND(AVG(Price), 2) AS median_price
                    FROM ranked
                    WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
                    GROUP BY City
                    ORDER BY median_price DESC; 
                """,
                "chart": "bar",
                "x": "City",
                "y": "median_price"
            },
            
            "10. How are properties distributed across price buckets?": {
            "sql": """
                    SELECT
                        CASE
                            WHEN Price < 500000 THEN 'Below 5L'
                            WHEN Price BETWEEN 500000 AND 1000000 THEN '5L - 10L'
                            WHEN Price BETWEEN 1000000 AND 2000000 THEN '10L - 20L'
                            ELSE 'Above 20L'
                        END AS price_bucket,
                        COUNT(*) AS property_count
                    FROM listings
                    GROUP BY price_bucket
                """,
                "chart": "pie",
                "x": "price_bucket",
                "y": "property_count"
        },
            
            "11. Average Days on Market by City": {
                "sql": """
                    SELECT
                        l.City,
                        AVG(s.Days_on_Market) AS average_days_on_market
                    FROM sales s
                    INNER JOIN listings l
                        ON s.Listing_ID = l.Listing_ID
                    GROUP BY l.City
                """,
                "chart": "bar",
                "x": "City",
                "y": "average_days_on_market"
            },

            "12. Fastest Selling Property Types": {
                "sql": """
                    SELECT
                        l.Property_Type,
                        AVG(s.Days_on_Market) AS average_days_on_market
                    FROM sales s
                    INNER JOIN listings l
                        ON s.Listing_ID = l.Listing_ID
                    GROUP BY l.Property_Type
                    ORDER BY average_days_on_market
                """,
                "chart": "bar",
                "x": "Property_Type",
                "y": "average_days_on_market"
            },

            "13. Percentage of Properties Sold Above Listing Price": {
                "sql": """
                    SELECT 
                        (COUNT(CASE WHEN s.Sale_Price > l.Price THEN 1 END) * 100.0) / COUNT(*) 
                            AS percent_sold_above_listing
                    FROM listings l
                    JOIN sales s
                        ON l.Listing_ID = s.Listing_ID;
                """,
                "chart": None
            },

            "14. Sale-to-List Price Ratio by City": {
                "sql": """
                    SELECT
                        l.City,
                        AVG(s.Sale_Price / l.Price) AS sale_to_list_ratio
                    FROM listings l
                    JOIN sales s
                        ON l.Listing_ID = s.Listing_ID
                    GROUP BY l.City
                """,
                "chart": "bar",
                "x": "City",
                "y": "sale_to_list_ratio"
            },

            "15. Listings Taking More Than 90 Days to Sell": {
                "sql": """
                    SELECT
                        l.Listing_ID,
                        l.City,
                        l.Property_Type,
                        s.Days_on_Market
                    FROM listings l
                    JOIN sales s
                        ON l.Listing_ID = s.Listing_ID
                    WHERE s.Days_on_Market > 90
                """,
                "chart": None
            },

            "16. Impact of Metro Distance on Time on Market": {
                "sql": """
                    SELECT
                        p.metro_distance_km,
                        AVG(s.Days_on_Market) AS avg_days_on_market
                    FROM property_attributes p
                    JOIN listings l
                        ON p.Listing_ID = l.Listing_ID
                    JOIN sales s
                        ON l.Listing_ID = s.Listing_ID
                    GROUP BY p.metro_distance_km
                    ORDER BY p.metro_distance_km
                """,
                "chart": "line",
                "x": "metro_distance_km",
                "y": "avg_days_on_market"
            },

            "17. Monthly Sales Trend": {
                "sql": """
                    SELECT
                        strftime('%Y-%m', Date_Sold) AS sale_month,
                        COUNT(*) AS total_sales
                    FROM sales
                    GROUP BY sale_month
                    ORDER BY sale_month
                """,
                "chart": "line",
                "x": "sale_month",
                "y": "total_sales"
            },

            "18. Properties Currently Unsold": {
                "sql": """
                    SELECT
                        l.Listing_ID,
                        l.City,
                        l.Property_Type,
                        l.Price
                    FROM listings l
                    LEFT JOIN sales s
                        ON l.Listing_ID = s.Listing_ID
                    WHERE s.Listing_ID IS NULL
                """,
                "chart": None
            },

            "19. Agents with Most Sales Closed": {
                "sql": """
                    SELECT
                        a.Agent_ID,
                        a.Name,
                        COUNT(s.Listing_ID) AS total_sales_closed
                    FROM agents a
                    JOIN listings l
                        ON a.Agent_ID = l.Agent_ID
                    JOIN sales s
                        ON l.Listing_ID = s.Listing_ID
                    GROUP BY a.Agent_ID, a.Name
                    ORDER BY total_sales_closed DESC
                """,
                "chart": "bar",
                "x": "Name",
                "y": "total_sales_closed"
            },

            "20. Top Agents by Total Sales Revenue": {
                "sql": """
                    SELECT
                        a.Agent_ID,
                        a.Name,
                        SUM(s.Sale_Price) AS total_sales_revenue
                    FROM agents a
                    JOIN listings l
                        ON a.Agent_ID = l.Agent_ID
                    JOIN sales s
                        ON l.Listing_ID = s.Listing_ID
                    GROUP BY a.Agent_ID, a.Name
                    ORDER BY total_sales_revenue DESC
                """,
                "chart": "bar",
                "x": "Name",
                "y": "total_sales_revenue"
            },
            
            "21. Which agents close deals fastest?": {
                "sql": """
                    SELECT
                        Agent_ID,
                        Name,
                        avg_closing_days
                    FROM agents
                    ORDER BY avg_closing_days ASC
                """,
                "chart": "bar",
                "x": "Name",
                "y": "avg_closing_days"
            },

            "22. Does experience correlate with deals closed?": {
                "sql": """
                    SELECT 
                        experience_years,
                        AVG(deals_closed) AS avg_deals_closed
                    FROM agents
                    GROUP BY experience_years
                    ORDER BY experience_years;
                """,
                "chart": "bar",
                "x": "experience_years",
                "y": "avg_deals_closed"
            },
            "23. Do agents with higher ratings close deals faster?": {
                "sql": """
                    SELECT 
                        Agent_ID,
                        Name,
                        rating,
                        avg_closing_days
                    FROM agents
                    ORDER BY rating DESC, avg_closing_days ASC;
                """,
                "chart": "bar",
                "x": "rating",
                "y": "avg_closing_days"
            },
             "24. What is the average commission earned by each agent?": {
                "sql": """
                    SELECT
                        a.Agent_ID,
                        a.Name,
                        AVG(s.Sale_Price * a.commission_rate) AS avg_commission
                    FROM agents a
                    JOIN listings l
                        ON a.Agent_ID = l.Agent_ID
                    JOIN sales s
                        ON l.Listing_ID = s.Listing_ID
                    GROUP BY a.Agent_ID, a.Name
                """,
                "chart": "bar",
                "x": "Name",
                "y": "avg_commission"
            },  
            "25. Which agents currently have the most active listings?": {
                "sql": """
                    SELECT 
                        a.Agent_ID,
                        a.Name,
                        COUNT(l.Listing_ID) AS active_listings
                    FROM agents a
                    JOIN listings l
                        ON a.Agent_ID = l.Agent_ID
                    LEFT JOIN sales s
                        ON l.Listing_ID = s.Listing_ID
                    WHERE s.Listing_ID IS NULL
                    GROUP BY a.Agent_ID, a.Name
                    ORDER BY active_listings DESC;
                """,
                "chart": "bar",
                "x": "Name",
                "y": "active_listings"
            },
            
            "26. What percentage of buyers are investors vs end users?": {
                "sql": """
                    SELECT
                        buyer_type,
                        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM buyers) AS percentage
                    FROM buyers
                    GROUP BY buyer_type
                """,
                "chart": "pie",
                "x": "buyer_type",
                "y": "percentage"
            },

            "27. Which cities have the highest loan uptake rate?": {
                "sql": """
                    SELECT
                        l.City,
                        COUNT(CASE WHEN b.loan_taken = 1 THEN 1 END) * 100.0 / COUNT(*) AS loan_uptake_rate
                    FROM buyers b
                    JOIN sales s
                        ON b.sale_id = s.Listing_ID
                    JOIN listings l
                        ON s.Listing_ID = l.Listing_ID
                    GROUP BY l.City
                    ORDER BY loan_uptake_rate DESC;
                """,
                "chart": "bar",
                "x": "City",
                "y": "loan_uptake_rate"
            },
            "28. What is the average loan amount by buyer type?": {
                    "sql": """
                        SELECT
                            buyer_type,
                            AVG(loan_amount) AS avg_loan_amount
                        FROM buyers
                        WHERE loan_taken = 1
                        GROUP BY buyer_type
                    """,
                    "chart": "bar",
                    "x": "buyer_type",
                    "y": "avg_loan_amount"
                },

            "29. Which payment mode is most commonly used?": {
                    "sql": """
                        SELECT
                            payment_mode,
                            COUNT(*) AS usage_count
                        FROM buyers
                        GROUP BY payment_mode
                        ORDER BY usage_count DESC
                    """,
                    "chart": "bar",
                    "x": "payment_mode",
                    "y": "usage_count"
                },

            "30. Do loan-backed purchases take longer to close?": {
                    "sql": """
                        SELECT
                            b.loan_taken,
                            AVG(s.Days_on_Market) AS avg_days_on_market
                        FROM buyers b
                        JOIN sales s
                            ON b.sale_id = s.Listing_ID
                        GROUP BY b.loan_taken
                    """,
                    "chart": "bar",
                    "x": "loan_taken",
                    "y": "avg_days_on_market"
            }
        }

        # ---------------- SELECT QUERY ---------------- #

        selected_query = st.selectbox(
            "Select a SQL Query",
            list(queries.keys())
        )

        query_info = queries[selected_query]

        # ---------------- RUN QUERY ---------------- #

        result_df = get_data(query_info["sql"])

        # ---------------- SHOW SQL (OPTIONAL BUT NICE) ---------------- #

        with st.expander("📜 View SQL Query"):
            st.code(query_info["sql"], language="sql")

        # ---------------- TABLE OUTPUT (ALWAYS) ---------------- #

        st.subheader("📋 Query Result Table")
        st.dataframe(result_df, use_container_width=True)

        # ---------------- VISUALIZATION ---------------- #

        if query_info["chart"] and not result_df.empty:

            st.subheader("📊 Visualization")

            if query_info["chart"] == "bar":
                st.bar_chart(
                    result_df.set_index(query_info["x"])[query_info["y"]]
                )

            elif query_info["chart"] == "line":
                result_df[query_info["x"]] = pd.to_datetime(result_df[query_info["x"]])
                st.line_chart(
                    result_df.set_index(query_info["x"])[query_info["y"]]
                )

            elif query_info["chart"] == "pie":
                fig, ax = plt.subplots()
                ax.pie(
                    result_df[query_info["y"]],
                    labels=result_df[query_info["x"]],
                    autopct="%1.1f%%"
                )
                st.pyplot(fig)
        st.download_button(
            "⬇️ Download CSV",
            result_df.to_csv(index=False),
            "query_results.csv",
            "text/csv"
        )
elif page == "Creator Info":

        st.title("🧑‍💻 Creator Information")

        st.markdown("---")

        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(
                "atharva_image.jpg",
                width=150
            )

        with col2:
            st.markdown("""
            ### Atharva Borawake
            **Python Developer**

            📊 Passionate about data-driven insights  
            🏢 Interested in real-world business analytics  
            🧠 Skilled in Python,SQL, AI, ML, DL ,Streamlit, and Data Visualization  
            """)

        st.markdown("---")

        st.markdown("## 📌 About the Project")
        st.write("""
        BrickView was developed as a data analytics project to demonstrate the use of:
        - Relational databases and SQL querying
        - Data transformation using Pandas
        - Interactive dashboards using Streamlit
        - Business-focused analytical thinking
        """)

        st.markdown("## 📫 Contact")
        st.markdown("""
        - 📧 [Email](atharvaborawake210@gmail.com) 
        - 💼 [LinkedIn](https://www.linkedin.com/in/atharva-borawake-76a370197/) 
        - 🧑‍💻 [GitHub](https://github.com/AtharvaBorawake) 
        """)

        st.success("Thank you for exploring BrickView!")