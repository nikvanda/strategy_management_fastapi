# Strategy Management API

## Project Overview

This project provides a REST API service for managing asset trading strategies.  
Users can create, simulate, and optimize their strategies based on historical market data.

---

## Technical Stack

- **Programming Language:** Python 3  
- **Web Framework:** Flask  
- **Database:** PostgreSQL  
- **Message Broker:** RabbitMQ  
- **Caching System:** Redis  
- **Containerization:** Docker  

---

## Features

1. **User Authentication and Authorization**  
   - JWT-based authentication  
   - Endpoints for user registration (`/auth/register`) and login (`/auth/login`)  

2. **Strategy Management**  
   - CRUD operations for user strategies  
   - Example JSON structures supported  

3. **Strategy Simulation**  
   - Endpoint: `/strategies/{id}/simulate`  
   - Accepts historical data in JSON format  
   - Performs simulation based on buy and sell conditions  
   - Returns simulation results in JSON  

4. **RabbitMQ Integration**  
   - On strategy create or update, publishes messages like:  
     `"User X created strategy Y"` or `"User X updated strategy Y"`  

5. **Redis Caching**  
   - Caches user strategy lists to reduce DB load  
   - Ensures cache invalidation on update or delete  

---

## Environment Variables and Configuration

This project requires an `.env` file containing environment variables for PostgreSQL, Redis, RabbitMQ, and JWT settings.

**Important:** A template `.env` file is provided in a Google Docs document.  
Please copy the template and fill in your credentials before running the project.

Access the `.env` template here:  
https://drive.google.com/file/d/1_1UZEFfIGQXK4UnzWLceq4ei845E6Vhw/view?usp=sharing

---

## Setup & Deployment Using Docker Compose

### Prerequisites

- Install [Docker](https://docs.docker.com/get-docker/) on your machine  
- Install [Docker Compose](https://docs.docker.com/compose/install/) (often included with Docker Desktop)

### Steps to Run

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-repo/strategy-management.git
   cd strategy-management

2. **Run docker**

   ```bash
   docker-compose up --build
   
3. **Use app**