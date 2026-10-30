# Procurement Sourcing Platform

A Django-based web application designed to connect business clients with suppliers and support a structured sourcing process.

**Developed as an independent portfolio project.**

## Project Overview

The Procurement Sourcing Platform aims to simplify the sourcing process by providing dedicated interfaces for clients and suppliers.

Clients can define their sourcing requirements, while suppliers can provide company information and details about their products and services.

The platform is designed to support transparent supplier collaboration and quotation evaluation.

## Main Interfaces

### 1. Home Page

* Main platform landing page.
* Separate navigation for Client and Supplier interfaces.
* Overview of the sourcing workflow.

### 2. Client Interface

* Company information form.
* Contact and delivery details.
* Product and service category selection.
* Additional sourcing requirements.

### 3. Supplier Interface

* Supplier company information.
* Product and service descriptions.
* Payment terms.
* Delivery terms.
* Additional supplier information.

## Screenshots

The application screenshots and detailed project documentation are available in:

[PROJECT_DOCUMENTATION.docx](PROJECT_DOCUMENTATION.docx)

## Technology Stack

* Python
* Django
* SQLite
* HTML
* CSS

## Project Structure

```text
procurement-sourcing-platform/
│
├── sourcing/
│   ├── migrations/
│   ├── templates/
│   ├── models.py
│   ├── views.py
│   ├── admin.py
│   └── tests.py
│
├── testsite/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── manage.py
├── .gitignore
├── README.md
└── PROJECT_DOCUMENTATION.docx
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/HoriaCT/procurement-sourcing-platform.git
```

### 2. Open the project folder

```bash
cd procurement-sourcing-platform
```

### 3. Install Django

```bash
python -m pip install django
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Start the development server

```bash
python manage.py runserver
```

### 6. Open the application

Visit:

http://127.0.0.1:8000/

## Future Development

The following features are planned for future versions:

* User account creation for clients and suppliers.
* Login and logout functionality.
* Role-based access control.
* Email verification and password recovery.
* Supplier account verification.
* Client sourcing request management.
* Supplier invitations and quotation submissions.
* Quotation comparison and supplier selection.
* Notifications and improved workflow tracking.

These features are planned enhancements and are not all implemented in the current version.

## Project Documentation

For additional details, application screenshots, and planned implementation features, see:

[Download Project Documentation](PROJECT_DOCUMENTATION.docx)

## Disclaimer

This is an independent educational and portfolio project. It is not an official Airbus application and is not affiliated with or endorsed by Airbus. No confidential company information is used.
