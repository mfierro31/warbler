"""User views tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Follows, Likes, connect_db

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserViewTestCase(TestCase):
    """Test message model."""
    def setUp(self):
        """Set up users, messages, likes, and follows"""
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.u = User(
            username="testuser",
            email="test@test.com",
            password="HASHED_PASSWORD",
        )

        self.u2 = User(
            username="testuser2", 
            email="test2@test.com", 
            password="HASHED_PASSWORD2", 
        )

        db.session.add_all([self.u, self.u2])
        db.session.commit()

        self.m = Message(text="Testing!", user_id=self.u.id)
        self.m2 = Message(text="Testing 2!", user_id=self.u2.id)

        db.session.add_all([self.m, self.m2])
        db.session.commit()

        self.u.followers.append(self.u2)
        self.u2.followers.append(self.u)
        self.u.following.append(self.u2)
        self.u2.following.append(self.u)

        self.u.likes.append(self.m2)
        self.u2.likes.append(self.m)

        db.session.add_all([self.u, self.u2])
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Remove any fouled transactions"""
        db.session.rollback()

    def test_logged_in_followers_following_pages(self):
        """If you're logged in, can you see another user's followers and following pages?"""
        with self.client.session_transaction() as change_session:
            change_session['curr_user'] = self.u.id

        resp = self.client.get(f"/users/{self.u2.id}/followers", follow_redirects=True)
        html = resp.get_data(as_text=True)

        resp2 = self.client.get(f"/users/{self.u2.id}/following", follow_redirects=True)
        html2 = resp2.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<p>@testuser</p>', html)

        self.assertEqual(resp2.status_code, 200)
        self.assertIn('<p>@testuser</p>', html2)