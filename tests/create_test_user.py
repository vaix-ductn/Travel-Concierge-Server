#!/usr/bin/env python3
"""
Script to create a test user for the Travel Concierge application
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from user_manager.models import User, UserProfile

def create_test_user():
    """Create a test user for login testing"""

    # Check if user already exists
    if User.objects.filter(username='nero').exists():
        print("User 'nero' already exists!")
        return

    # Create the user
    user = User.objects.create(
        username='nero',
        email='tranamynero@gmail.com',
        password=make_password('1234@pass'),
        full_name='Nero Tran'
    )

    # Create user profile
    profile = UserProfile.objects.create(
        user=user,
        address='Ha Noi, Viet Nam',
        interests='Travel, Photography, Food',
        avatar_url='',
        passport_nationality='Vietnamese',
        seat_preference='window',
        food_preference='Japanese cuisine - Ramen, Sushi, Sashimi',
        allergies=[],
        likes=['temples', 'beaches', 'mountains', 'museums', 'nightlife', 'hiking', 'hot springs', 'beautiful scenery'],
        dislikes=['remote locations', 'dangerous areas', 'places unsuitable for families with small children'],
        price_sensitivity=['mid-range'],
        home_address='2-chōme-40-2 Harayama, Midori Ward, Saitama, 336-0931',
        local_prefer_mode='drive'
    )

    print(f"✅ Test user 'nero' created successfully!")
    print(f"   Username: nero")
    print(f"   Password: 1234@pass")
    print(f"   Email: {user.email}")

if __name__ == '__main__':
    create_test_user()