# C$50 Finance

A web-based stock trading simulator implemented as part of Harvard's CS50x course (Problem Set 9).
This application allows users to register, get real-time stock quotes, "buy" and "sell" stocks using virtual currency, and view their transaction history

## Project overview

While the initial distribution code (CSS, basic layout, and helper functions) was provided by the course staff, **I was responsible for implementing the core back-end logic, database interactions, and dynamic templates.**

### Features I implemented

I developed the following functionalities using **Python (Flask)** and **SQL**:

* **Registration (`/register`):** Created logic to register new users, ensuring username uniqueness and secure password hashing.
* **Quoting (`/quote`):** Implemented a feature to fetch current stock prices via an API.
* **Buying (`/buy`):** Built the logic to allow users to purchase stocks. This involves:
    * Checking current stock price.
    * Verifying the user has enough cash.
    * Updating the database (deducting cash, adding shares) transactionally.
* **Selling (`/sell`):** Created the functionality for users to sell shares they own, updating their cash balance and portfolio accordingly.
* **Index/Portfolio (`/`):** Designed the main dashboard to display a summary of the user's current holdings, cash balance, and total based on live stock prices.
* **History (`/history`):** Implemented a transaction log showing all past buys and sells for the logged-in user.

## Tech Stack

* **Back-end:** Python, Flask
* **Database:** SQLite
* **Front-end:** HTML, Jinja2 templates, CSS
* **API:** IEX Cloud (for stock data)

## Disclaimer

This project is a solution to a CS50 problem set. The distribution code (including `helpers.py` and static assets) is owned by CS50. The implementation of the routes and database logic is my own work.
