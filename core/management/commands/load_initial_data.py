from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from core.models import PricingPackage, PricingFeature

class Command(BaseCommand):
    help = 'Loads initial data for the pricing packages'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Creating initial pricing packages...'))
        
        # Create Standard Package
        standard_package, created = PricingPackage.objects.update_or_create(
            package_type='standard',
            defaults={
                'name': _('სტანდარტული'),
                'original_price': 40.00,
                'current_price': 0.00,
                'is_free': True,
                'description': _('იდეალურია დამწყები კომპანიებისთვის'),
                'display_order': 1,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created standard package: {str(standard_package.name)}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated standard package: {str(standard_package.name)}'))
        
        # Standard package features
        standard_features = [
            {'text': _('1 განცხადება - პერიოდი 30 დღე'), 'is_included': True},
            {'text': _('მთავარ გვერდზე ყოფნა'), 'is_included': False},
            {'text': _('ლოგოს გამოჩენა'), 'is_included': True},
            {'text': _('დამსაქმებლის პროფილი და სივების ანალიტიკა'), 'is_included': True},
            {'text': _('ძიებისას პრიორიტეტულობა: დაბალი'), 'is_included': True},
        ]
        
        # Delete existing features
        PricingFeature.objects.filter(package=standard_package).delete()
        
        # Create new features
        for i, feature in enumerate(standard_features):
            PricingFeature.objects.create(
                package=standard_package,
                text=feature['text'],
                is_included=feature['is_included'],
                display_order=i+1
            )
        
        # Create Premium Package
        premium_package, created = PricingPackage.objects.update_or_create(
            package_type='premium',
            defaults={
                'name': _('პრემიუმი'),
                'original_price': 95.00,
                'current_price': 50.00,
                'is_popular': True,
                'description': _('იდეალურია აქტიური დამსაქმებლებისთვის'),
                'display_order': 2,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created premium package: {str(premium_package.name)}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated premium package: {str(premium_package.name)}'))
        
        # Premium package features
        premium_features = [
            {'text': _('1 განცხადება - პერიოდი 30 დღე'), 'is_included': True},
            {'text': _('მთავარი გვერდის მეორე სექცია'), 'is_included': True},
            {'text': _('ლოგოს გამოჩენა'), 'is_included': True},
            {'text': _('სოც. ქსელებში გაზიარება ჯგუფური პოსტის სახით'), 'is_included': True},
            {'text': _('პრემიუმის ნიშანი'), 'is_included': True},
            {'text': _('ვაკანსიის ატვირთვა Karriera.ge-ზე'), 'is_included': True},
            {'text': _('ძიებისას პრიორიტეტულობა: საშუალო'), 'is_included': True},
            {'text': _('დამსაქმებლის პროფილი და სივების ანალიტიკა'), 'is_included': True},
            {'text': _('სივების ბაზაზე წვდომა'), 'is_included': True},
        ]
        
        # Delete existing features
        PricingFeature.objects.filter(package=premium_package).delete()
        
        # Create new features
        for i, feature in enumerate(premium_features):
            PricingFeature.objects.create(
                package=premium_package,
                text=feature['text'],
                is_included=feature['is_included'],
                display_order=i+1
            )
        
        # Create Premium Plus Package
        premium_plus_package, created = PricingPackage.objects.update_or_create(
            package_type='premium_plus',
            defaults={
                'name': _('პრემიუმ+'),
                'original_price': 120.00,
                'current_price': 60.00,
                'description': _('იდეალურია მაღალი კონკურენციის პოზიციებისთვის'),
                'display_order': 3,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created premium plus package: {str(premium_plus_package.name)}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated premium plus package: {str(premium_plus_package.name)}'))
        
        # Premium Plus package features
        premium_plus_features = [
            {'text': _('1 განცხადება - პერიოდი 30 დღე'), 'is_included': True},
            {'text': _('მთავარი გვერდის პირველი სექცია'), 'is_included': True},
            {'text': _('ლოგოს გამოჩენა'), 'is_included': True},
            {'text': _('სოც. ქსელებში გაზიარება ინდივიდუალური და ჯგუფური პოსტის სახით'), 'is_included': True},
            {'text': _('პრემიუმ+ ნიშანი'), 'is_included': True},
            {'text': _('ვაკანსიის ატვირთვა Karriera.ge-ზე'), 'is_included': True},
            {'text': _('ძიებისას პრიორიტეტულობა: მაღალი'), 'is_included': True},
            {'text': _('დამსაქმებლის პროფილი და სივების ანალიტიკა'), 'is_included': True},
            {'text': _('სივების ბაზაზე წვდომა'), 'is_included': True},
            {'text': _('სპეციალური გვერდი კომპანიისთვის'), 'is_included': True},
        ]
        
        # Delete existing features
        PricingFeature.objects.filter(package=premium_plus_package).delete()
        
        # Create new features
        for i, feature in enumerate(premium_plus_features):
            PricingFeature.objects.create(
                package=premium_plus_package,
                text=feature['text'],
                is_included=feature['is_included'],
                display_order=i+1
            )
        
        self.stdout.write(self.style.SUCCESS('Successfully created pricing packages and features.')) 