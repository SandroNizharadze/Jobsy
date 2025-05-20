from django.core.management.base import BaseCommand
from core.models import RejectionReason
from django.utils.translation import gettext_lazy as _

class Command(BaseCommand):
    help = 'Adds initial rejection reasons to the database'

    def handle(self, *args, **options):
        # Define the rejection reasons
        reasons = [
            _("არასაკმარისი გამოცდილება"),
            _("უნარების ნაკლებობა"),
            _("განათლების შეუსაბამობა"),
            _("არარელევანტური სამუშაო ისტორია"),
            _("ლოკაცია"),
            _("სერთიფიკატების/ლიცენზიების ნაკლებობა"),
            _("მოთხოვნებთან შეუსაბამო მიღწევები"),
            _("სივის ფორმატის/სტრუქტურის ხარვეზები"),
            _("არასაკმარისი ინფორმაცია"),
            _("გადაჭარბებული ინფორმაცია"),
            _("კარიერული მიზნების შეუსაბამობა"),
            _("ენის ცოდნის ნაკლებობა"),
            _("არარეალისტური ხელფასის მოლოდინი"),
        ]
        
        # Add each reason to the database if it doesn't already exist
        count = 0
        for reason in reasons:
            obj, created = RejectionReason.objects.get_or_create(name=reason)
            if created:
                count += 1
                self.stdout.write(self.style.SUCCESS(f'Added rejection reason: "{reason}"'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully added {count} new rejection reasons')) 