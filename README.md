# AI-Driven Multi-Cloud High Availability and Automatic Failover System

## Project Overview

The **AI-Driven Multi-Cloud High Availability and Automatic Failover System** is a final-year engineering project designed to improve application availability through cloud health monitoring, failure detection, AI-based prediction, and automatic traffic failover.

This project is designed to improve the availability and reliability of web applications by deploying them across multiple cloud platforms. It uses Amazon Web Services (AWS) as the primary cloud environment and Google Cloud Platform (GCP) as the backup environment.

The system continuously monitors application health and performance metrics. When it detects a failure in the primary cloud environment, it automatically switches application traffic to the backup cloud environment to help maintain service availability.

## Architecture

- **Primary cloud:** AWS
- **Backup cloud:** Google Cloud Platform (GCP)
- **Backend:** Python and Flask
- **Database:** SQLite (current demo configuration)
- **Traffic routing:** Nginx
- **Monitoring:** Health metrics and cloud health checks
- **Notifications:** Telegram Bot API
- **Testing:** pytest

## Key Features

### 1. Cloud Health Monitoring
- Monitors primary and backup cloud nodes.
- Checks cloud instance status and application endpoint health.
- Collects CPU, memory, disk, and response-time metrics.

### 2. Failure Detection and Prediction
- Evaluates node health using configured thresholds.
- Provides AI-based failure prediction through the monitoring service.
- Records detected node failures.

### 3. Automatic Failover
- Detects a failed primary node through the monitoring workflow.
- Invokes the failover service when automatic failover is enabled.
- Switches traffic from AWS to the GCP backup environment.
- Verifies the active traffic route after switching.

### 4. Monitoring Dashboard
- Displays cloud-node status.
- Shows health metrics and AI predictions.
- Displays recorded failover events.

### 5. Telegram Notifications
- Sends application startup notifications.
- Sends monitoring and failover notifications.
- Sends API and cloud-health diagnostic summaries.

### 6. Event Logging
- Records node failure and failover events.
- Maintains a history of successful and incomplete failover attempts.

## System Workflow

1. The monitoring system collects health information.
2. The monitoring service evaluates node status.
3. A failed primary node is identified.
4. Automatic failover is triggered when enabled.
5. The backup cloud provider performs the traffic switch.
6. The system verifies the active route.
7. The event is recorded and notifications are sent.

## Technologies Used

| Component | Technology |
|---|---|
| Programming language | Python |
| Backend framework | Flask |
| Primary cloud | AWS |
| Backup cloud | Google Cloud Platform |
| Traffic management | Nginx |
| Database | SQLite |
| Monitoring | psutil and cloud health APIs |
| Notifications | Telegram Bot API |
| Testing | pytest |
| Frontend | HTML, CSS, JavaScript |

## Project Structure

```text
AI-multi-cloud-failover-system/
├── app/
│   ├── api/
│   ├── infrastructure/
│   │   └── cloud_providers/
│   ├── models/
│   ├── services/
│   ├── static/
│   └── templates/
├── scripts/
│   └── api_connection_check.py
├── tests/
│   └── unit/
├── instance/
├── migrations/
├── monitoring_agent/
├── ml/
├── run.py
├── requirements.txt
├── .env.example
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/naveen-varu/AI-multi-cloud-failover-system.git
cd AI-multi-cloud-failover-system
```

### 2. Create a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file using `.env.example` as a reference.

Configure the required application, AWS, GCP, database, failover, and notification settings.

**Never commit `.env` or real cloud credentials to GitHub.**

### 5. Configure cloud access

Configure AWS and GCP permissions and credentials appropriate to your deployment environment. The application must have permission to perform the required cloud health checks and failover operations.

### 6. Start the application

```bash
python run.py
```

The Flask application runs on port 5000.

## Running Tests

Run the unit test suite:

```bash
python -m pytest -v
```

### Latest Test Results

- Total tests: 17
- Passed: 17
- Failed: 0

Three non-blocking warnings were reported during the test run, including Python 3.10 support notices from Google Cloud libraries and a SQLAlchemy legacy API warning.

## API and Diagnostics

The project provides APIs for node management, health monitoring, metrics, cloud configuration, and failover event history.

A read-only diagnostic script is included:

```bash
python scripts/api_connection_check.py
```

The script checks the Flask application, selected APIs, protected failover event access, and AWS/GCP health endpoints. It can send a consolidated diagnostic summary through Telegram.

## Demonstration Results

The automatic failover workflow was successfully demonstrated using a controlled synthetic AWS CPU failure.

During the demonstration:

1. AWS was configured as the primary node.
2. GCP was configured as the backup node.
3. A synthetic CPU failure metric was submitted for the AWS node.
4. The monitoring service identified the primary node as failed.
5. Automatic failover was triggered.
6. Traffic was switched to the GCP backup.
7. The active route was verified successfully.
8. The failover event was recorded.

**Note:** This was a controlled failure simulation. It does not represent testing during an actual AWS infrastructure outage.

## Current Project Status

The core academic demonstration has been implemented and tested:

- AWS primary and GCP backup integration
- Cloud health monitoring
- Health metric APIs
- Failure detection
- AI-based prediction integration
- Automatic failover workflow
- Nginx traffic switching and verification
- Dashboard event history
- Telegram notifications
- API diagnostics
- Unit test suite

## Expected Outcome
The project demonstrates how multiple cloud environments can work together to improve application availability, reduce dependence on a single cloud provider, and support automatic recovery when the primary environment experiences a failure.
#### Applications and Use Cases

This application can be used in environments where continuous service availability and minimal downtime are important.

1. **E-commerce Platforms**
   Helps keep online shopping websites available during cloud server failures, so customers can continue browsing and placing orders.

2. **Banking and Financial Applications**
   Supports the availability of online banking services, payment systems, and financial applications by switching traffic to a backup environment when a primary service fails.

3. **Healthcare Systems**
   Can help maintain access to hospital management systems, appointment portals, and other healthcare applications that need reliable availability.

4. **Educational Platforms**
   Helps online learning portals, examination systems, and student management applications remain accessible during infrastructure failures.

5. **Enterprise Applications**
   Supports business-critical applications such as employee portals, customer relationship management systems, and internal business tools.

6. **Cloud-Based Web Applications**
   Provides an automatic failover mechanism for applications deployed across multiple cloud providers, reducing dependence on a single cloud environment.

7. **Disaster Recovery and Business Continuity**
   Can be used as part of a disaster recovery strategy by redirecting application traffic to a healthy backup environment when the primary environment becomes unavailable.

**Note:** This project demonstrates automatic failover from an AWS primary environment to a GCP backup environment. The examples above describe potential application areas; they are not claims of production deployment or certification.

## Limitations and Future Improvements

- Test failover under additional real-world cloud failure scenarios.
- Improve continuous metric collection and visualization.
- Upgrade the Python runtime to a currently supported version.
- Improve dashboard authentication and access control.
- Add more cloud-provider integrations.
- Expand integration and end-to-end testing.

## Author

**Naveen H T**

Repository: https://github.com/naveen-varu/AI-multi-cloud-failover-system
## Connect With Me

- Instagram: [@_naveen_i54](https://www.instagram.com/_naveen_i54/)
- GitHub: [https://github.com/naveen-varu](https://github.com/naveen-varu)
