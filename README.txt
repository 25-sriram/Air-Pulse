# ✈️ Air-Pulse — Airfare Intelligence & Prediction System

> A data-driven airfare intelligence platform that analyzes historical flight fares, identifies booking patterns, calculates airfare price indices, predicts future fares, and provides actionable booking recommendations.

---

## 📌 Overview

**Air-Pulse** is an airfare intelligence and decision-support platform developed to understand how airline ticket prices change across different routes and booking windows.

The system combines:

- Flight fare data
- Data cleaning and preprocessing
- Route-level fare analysis
- Lead-time analysis
- Monthly Airfare Price Index
- Fare heatmap visualization
- Machine Learning-based fare prediction
- Booking window recommendations
- MySQL-based data management
- Interactive web dashboard

The main objective of Air-Pulse is to transform raw airfare observations into meaningful insights that can help users understand **when and where airfare prices are likely to be favorable**.

The current prototype focuses on a **three-month dataset** and is designed so that the system can later be extended to larger historical datasets.

---

## 🎯 Problem Statement

Airfare prices are dynamic and can vary depending on:

- Route
- Airline
- Booking lead time
- Travel date
- Demand
- Market conditions
- Other pricing factors

For a traveler, simply knowing the current ticket price does not answer an important question:

> **"Is this a good time to book?"**

Air-Pulse attempts to answer this question by analyzing historical fare behavior and presenting the information through an easy-to-understand dashboard.

---

## 💡 Proposed Solution

Air-Pulse processes collected airfare observations and converts them into several analytical features.

The platform provides:

1. **Market Fare Analysis**
2. **Route-level Fare Comparison**
3. **Lead-Time Fare Analysis**
4. **Monthly Airfare Price Index**
5. **Fare Heatmap**
6. **Machine Learning Fare Predictions**
7. **Booking Recommendations**

These features work together to provide a broader understanding of airfare behavior rather than relying only on a single ticket price.

---

# 🏗️ System Architecture

```text
                    ┌──────────────────────┐
                    │   Airfare Sources    │
                    │  IGNAV / DGCA Data   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Data Collection      │
                    │ multi_route_collector│
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Data Cleaning        │
                    │ data_cleaning.py     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      MySQL           │
                    │    airfare_db        │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
             ▼                 ▼                 ▼
      ┌─────────────┐   ┌──────────────┐  ┌──────────────┐
      │ Fare        │   │ Monthly      │  │ ML Fare      │
      │ Analysis    │   │ Price Index  │  │ Prediction   │
      └──────┬──────┘   └──────┬───────┘  └──────┬───────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Flask REST APIs      │
                    │       app.py         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Interactive Dashboard│
                    │ HTML + CSS + JS      │
                    │      Chart.js        │
                    └──────────────────────┘
