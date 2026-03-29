from django.core.management.base import BaseCommand
from django.utils import timezone
from food.models import Food


class Command(BaseCommand):
    help = 'Delete expired food items'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_food = Food.objects.filter(expiry_time__lt=now)
        count = expired_food.count()
        expired_food.delete()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} expired food items')
        )