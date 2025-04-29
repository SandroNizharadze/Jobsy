import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import JobListing, UserProfile, EmployerProfile

class Command(BaseCommand):
    help = 'Populates the database with sample job listings'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=10, help='Number of job listings to create')

    def handle(self, *args, **options):
        count = options['count']
        
        # Check if we have employers
        employers = EmployerProfile.objects.all()
        if not employers.exists():
            self.stdout.write(self.style.WARNING('No employer profiles found. Creating sample employers first.'))
            self._create_employers()
            employers = EmployerProfile.objects.all()
        
        # Create job listings
        for i in range(count):
            employer = random.choice(employers)
            job = self._create_job(employer, i)
            self.stdout.write(self.style.SUCCESS(f'Created job: {job.title} at {job.company}'))
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {count} job listings'))

    def _create_employers(self):
        """Create some sample employer profiles"""
        companies = [
            {
                'name': 'ТехГрузия',
                'website': 'https://techgeorgia.ge',
                'description': 'ТехГрузия - ведущая технологическая компания в Грузии, фокусирующаяся на разработке инновационных программных решений.',
                'industry': 'IT და პროგრამული უზრუნველყოფა',
                'size': '50-200',
                'location': 'თბილისი',
            },
            {
                'name': 'მედიკალ სისტემს',
                'website': 'https://medicalsystems.ge',
                'description': 'მედიკალ სისტემს არის ჯანდაცვის ტექნოლოგიების კომპანია, რომელიც ქმნის პროგრამულ უზრუნველყოფას ჯანდაცვის დაწესებულებებისთვის.',
                'industry': 'ჯანდაცვა',
                'size': '20-50',
                'location': 'თბილისი',
            },
            {
                'name': 'საფინანსო ჰაბი',
                'website': 'https://finhub.ge',
                'description': 'საფინანსო ჰაბი არის ფინტექ კომპანია, რომელიც აერთიანებს საფინანსო ტექნოლოგიებს და ინოვაციურ საბანკო მომსახურებას.',
                'industry': 'ფინანსები და საბანკო საქმე',
                'size': '100-500',
                'location': 'ბათუმი',
            },
            {
                'name': 'DigitalMinds',
                'website': 'https://digitalminds.ge',
                'description': 'DigitalMinds სპეციალიზირდება ციფრულ მარკეტინგსა და ვებ-განვითარებაში, ვქმნით ინოვაციურ ციფრულ გამოცდილებას.',
                'industry': 'მარკეტინგი და რეკლამა',
                'size': '10-20',
                'location': 'თბილისი',
            },
            {
                'name': 'EcoTech Georgia',
                'website': 'https://ecotech.ge',
                'description': 'EcoTech Georgia მუშაობს მდგრადი ტექნოლოგიების განვითარებაზე გარემოს დაცვის მიმართულებით.',
                'industry': 'მწვანე ტექნოლოგიები',
                'size': '20-50',
                'location': 'ქუთაისი',
            },
        ]
        
        # Create or get admin user
        admin_user, created = User.objects.get_or_create(
            username='admin@example.com',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            admin_user.set_password('adminpassword')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user: admin@example.com'))
        
        # Make sure admin has a user profile
        admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        
        # Create employers for each company
        for idx, company in enumerate(companies):
            # Create user for this employer
            email = f"employer{idx+1}@example.com"
            employer_user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': f'Employer',
                    'last_name': f'{idx+1}',
                }
            )
            
            if created:
                employer_user.set_password('password123')
                employer_user.save()
                self.stdout.write(self.style.SUCCESS(f'Created employer user: {email}'))
            
            # Get or create employer profile
            user_profile, _ = UserProfile.objects.get_or_create(user=employer_user)
            user_profile.role = 'employer'
            user_profile.save()
            
            employer_profile, created = EmployerProfile.objects.get_or_create(
                user_profile=user_profile,
                defaults={
                    'company_name': company['name'],
                    'company_website': company['website'],
                    'company_description': company['description'],
                    'industry': company['industry'],
                    'company_size': company['size'],
                    'location': company['location'],
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created employer profile: {company["name"]}'))
            else:
                # Update existing profile
                for key, value in company.items():
                    setattr(employer_profile, f'company_{key}' if key != 'industry' and key != 'location' else key, value)
                employer_profile.save()
                self.stdout.write(self.style.SUCCESS(f'Updated employer profile: {company["name"]}'))

    def _create_job(self, employer, index):
        """Create a sample job listing"""
        job_titles = [
            'Python დეველოპერი',
            'ფროენდ დეველოპერი',
            'მობაილ დეველოპერი (iOS/Android)',
            'DevOps ინჟინერი',
            'React დეველოპერი',
            'ფულსთეკ დეველოპერი',
            'UI/UX დიზაინერი',
            'დატა ანალიტიკოსი',
            'პროდუქტის მენეჯერი',
            'QA ინჟინერი',
            'Java დეველოპერი',
            'მარკეტინგის სპეციალისტი',
            'ფინანსური ანალიტიკოსი',
            'HR მენეჯერი',
            'კონტენტის მენეჯერი',
        ]
        
        experience_levels = [
            'ენთუზიასტი',
            'დამწყები',
            'საშუალო დონე',
            'გამოცდილი',
            'ექსპერტი',
        ]
        
        job_descriptions = [
            """ჩვენ ვეძებთ გამოცდილ Python დეველოპერს, რომელიც შეუერთდება ჩვენს გუნდს ინოვაციური პროექტების შესაქმნელად. ძირითადი პასუხისმგებლობები:
- ბექენდის განვითარება Django ან Flask-ზე
- RESTful API-ების შექმნა და მხარდაჭერა
- მონაცემთა ბაზებთან მუშაობა (PostgreSQL, MongoDB)
- ბიზნეს ლოგიკის იმპლემენტაცია და ოპტიმიზაცია
- ახალი ფუნქციონალის დაგეგმვა და განხორციელება
- TDD და ხარისხის კონტროლი

მოთხოვნები:
- 2+ წლიანი გამოცდილება Python-ში
- Django ან Flask-ის ცოდნა
- RESTful API-ების გამოცდილება
- მონაცემთა ბაზების გამოცდილება
- ინგლისური ენის ცოდნა
            """,
            
            """გვესაჭიროება კრეატიული და გამოცდილი UI/UX დიზაინერი პროდუქტების დასახვეწად. ძირითადი პასუხისმგებლობები:
- მომხმარებელზე ორიენტირებული ინტერფეისების დიზაინი
- პროტოტიპების შექმნა და იტერაცია
- დიზაინის სისტემების განვითარება
- პროდუქტის გუნდთან თანამშრომლობა
- მომხმარებელთა გამოცდილების ანალიზი

მოთხოვნები:
- 3+ წლიანი გამოცდილება UI/UX დიზაინში
- Figma, Sketch ან ანალოგიური ინსტრუმენტები
- მომხმარებელთა კვლევის გამოცდილება
- დიზაინის სისტემებთან მუშაობის გამოცდილება
            """,
            
            """ვეძებთ მოტივირებულ მარკეტინგის სპეციალისტს, რომელიც დაგვეხმარება ბრენდის განვითარებაში. ძირითადი პასუხისმგებლობები:
- სოციალური მედიის კამპანიების დაგეგმვა და განხორციელება
- კონტენტის შექმნა და მართვა
- ანალიტიკის მონიტორინგი და ანგარიშგება
- პარტნიორებთან ურთიერთობა
- ბაზრის კვლევა და კონკურენტების ანალიზი

მოთხოვნები:
- 1+ წლიანი გამოცდილება დიჯიტალ მარკეტინგში
- Facebook, Instagram და Google Ads-ის ცოდნა
- ანალიტიკური უნარები
- კრეატიული აზროვნება
            """,
            
            """გვჭირდება გამოცდილი მობაილ დეველოპერი, რომელსაც აქვს ნატიური აპლიკაციების განვითარების გამოცდილება. ძირითადი პასუხისმგებლობები:
- iOS/Android აპლიკაციების განვითარება
- აპლიკაციების მხარდაჭერა და გაუმჯობესება
- კოდის ხარისხის კონტროლი
- ახალი ტექნოლოგიების კვლევა და ინტეგრაცია
- ბექენდთან ინტეგრაცია

მოთხოვნები:
- 3+ წლიანი გამოცდილება მობაილ დეველოპმენტში
- Swift/Kotlin-ის ცოდნა
- REST API-სთან მუშაობის გამოცდილება
- მობაილური UI/UX პრინციპების ცოდნა
            """,
            
            """ვეძებთ პროაქტიულ და ორგანიზებულ HR მენეჯერს, რომელიც უზრუნველყოფს კომპანიის პერსონალის ეფექტურ მართვას. ძირითადი პასუხისმგებლობები:
- რეკრუტმენტის პროცესების მართვა
- თანამშრომელთა ონბორდინგი და განვითარება
- HR პოლიტიკისა და პროცედურების შემუშავება
- თანამშრომელთა კმაყოფილების მონიტორინგი
- შრომითი ურთიერთობების მართვა

მოთხოვნები:
- 2+ წლიანი გამოცდილება HR სფეროში
- რეკრუტმენტის პროცესების ცოდნა
- თანამშრომელთა შეფასების სისტემების ცოდნა
- კომუნიკაციისა და ინტერპერსონალური უნარები
            """,
        ]
        
        fields = [
            'პროგრამირება',
            'დიზაინი',
            'მარკეტინგი',
            'მობაილ დეველოპმენტი',
            'ადამიანური რესურსები',
            'ფინანსები',
            'პროდუქტის მენეჯმენტი',
            'ფრონტენდ დეველოპმენტი',
            'ბექენდ დეველოპმენტი',
            'დატა ანალიზი',
        ]
        
        interests = [
            'Python Django React',
            'HTML CSS JavaScript',
            'UI UX Figma',
            'SEO SEM Social Media',
            'Swift Kotlin Mobile',
            'Recruitment HR Development',
            'Financial Analysis Excel',
            'Product Management Agile',
            'Frontend React Vue Angular',
            'Backend Node.js Express',
            'Data Analysis SQL',
        ]
        
        job_preferences = [
            'სრული განაკვეთი',
            'ნახევარი განაკვეთი',
            'რემოუტი',
            'ჰიბრიდული',
            'ფრილანსი',
        ]
        
        # Random datetime in the last 30 days
        random_days = random.randint(0, 30)
        posted_at = timezone.now() - timedelta(days=random_days)
        
        # Create the job listing
        job = JobListing.objects.create(
            title=random.choice(job_titles),
            company=employer.company_name,
            description=random.choice(job_descriptions),
            interests=random.choice(interests),
            fields=random.choice(fields),
            experience=random.choice(experience_levels),
            job_preferences=random.choice(job_preferences),
            salary_min=random.randint(800, 3000),
            salary_max=random.randint(3000, 8000),
            salary_type='თვეში',
            category='IT და პროგრამული უზრუნველყოფა',
            location=employer.location or 'თბილისი',
            employer=employer,
            posted_at=posted_at,
        )
        
        return job 