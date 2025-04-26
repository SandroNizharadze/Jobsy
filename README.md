# LinkedAI - AI-Powered Job Platform

LinkedAI is a modern job platform that leverages artificial intelligence to connect job seekers with employers. The platform provides intelligent job matching, AI-powered career guidance, and a seamless job application process.

<img width="1141" alt="image" src="https://github.com/user-attachments/assets/e2682ced-68cc-4c24-be1d-0861e24e5511" />


<img width="1108" alt="image" src="https://github.com/user-attachments/assets/b80542b8-5caa-48d2-bf97-1a44b8b2a3be" />



## Features

### For Job Seekers
- **AI-Powered Job Matching**: Get personalized job recommendations based on your profile
- **Career Assistant**: Chat with an AI assistant for career guidance and advice
- **Profile Management**: Create and manage your professional profile
- **Job Applications**: Easy application process with resume and cover letter submission

### For Employers
- **Job Posting**: Create and manage job listings
- **Company Profile**: Showcase your company with detailed information
- **Dashboard**: Manage all your job postings in one place
- **AI Integration**: Get AI-powered insights for your job postings

## Tech Stack

- **Backend**: Django 5.1.7
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: PostgreSQL
- **Authentication**: Django's built-in authentication + Google OAuth2
- **AI Integration**: Custom AI chatbot for career guidance (llama3)

## AI Setup

The project uses llama3 for AI-powered features. Here's how to set it up:

### Prerequisites
- [Ollama](https://ollama.ai/) installed on your system
- At least 8GB of RAM (16GB recommended)

### Installation Steps

1. Install Ollama:
```bash
brew install ollama
```

2. Pull the llama3 model:
```bash
ollama pull llama3
```

3. Start the Ollama service:
```bash
ollama serve
```


 Test the AI integration:
- Start your Django development server
- Log in to the application
- Navigate to the AI Chat feature
- Try sending a message to verify the AI is responding


### AI Features

The AI integration provides:
- Career guidance and advice
- Job matching based on user profiles
- Resume analysis and suggestions
- Interview preparation tips
- Industry insights and trends

## Installation

1. Clone the repository:
```bash
git clone https://github.com/SandroNizharadze/LinkedAI.git
cd LinkedAI
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python manage.py migrate
```

5. Create a superuser:
```bash
python manage.py createsuperuser
```

6. Configure environment variables:
Create a `.env` file in the project root with the following variables:
```
DEBUG=True
SECRET_KEY=your_secret_key
DATABASE_URL=postgres://user:password@localhost:5432/linked_ai_db
GOOGLE_OAUTH2_KEY=your_google_oauth2_key
GOOGLE_OAUTH2_SECRET=your_google_oauth2_secret
```

7. Run the development server:
```bash
python manage.py runserver
```


## Key Features Implementation

### Job Listings
- Job creation and management

<img width="1159" alt="image" src="https://github.com/user-attachments/assets/18f7a349-e8e6-48c2-8522-798d2feaa45e" />

- Detailed job pages

<img width="1113" alt="image" src="https://github.com/user-attachments/assets/7af70acb-f3a0-49c8-9add-ef616b5460ac" />


### User Profiles
- Role-based access (Job Seeker/Employer)

<img width="1186" alt="image" src="https://github.com/user-attachments/assets/d022d868-625d-43ea-b493-7ced281bc562" />

<img width="1105" alt="image" src="https://github.com/user-attachments/assets/4750605f-70da-4cb1-be56-1564f3292f47" />


- Profile completion tracking
- Company profiles for employers

### Admin Profile
- Django administration interface


<img width="1512" alt="image" src="https://github.com/user-attachments/assets/a19bbe0e-7a9c-414e-91b4-ec734674eb31" />


### AI Integration
- Career guidance chatbot
- Job matching algorithm


<img width="1053" alt="image" src="https://github.com/user-attachments/assets/2cba8697-8b99-4509-a048-f3499b94f5b4" />




