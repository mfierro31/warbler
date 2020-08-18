"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, Follows

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


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(self.u)
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Remove any fouled transactions"""
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        # User should have no messages & no followers
        self.assertEqual(len(self.u.messages), 0)
        self.assertEqual(len(self.u.followers), 0)

    def test_repr_method(self):
        """Does repr method work as intended?"""
        self.assertEqual(self.u.__repr__(), f"<User #{self.u.id}: testuser, test@test.com>")

    def test_is_following_true(self):
        """Does is_following method work as intended for a true result?"""
        u2 = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
        db.session.add(u2)
        db.session.commit()

        self.u.following.append(u2)
        db.session.add(self.u)
        db.session.commit()

        self.assertEqual(self.u.is_following(u2), True)

    def test_is_following_false(self):
        """Does is_following method work as intended for a false result?"""
        u2 = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
        db.session.add(u2)
        db.session.commit()

        self.assertEqual(self.u.is_following(u2), False)

    def test_is_followed_by_true(self):
        """Does is_followed_by method work as intended for a true result?"""
        u2 = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
        db.session.add(u2)
        db.session.commit()

        self.u.followers.append(u2)
        db.session.add(self.u)
        db.session.commit()

        self.assertEqual(self.u.is_followed_by(u2), True)

    def test_is_followed_by_false(self):
        """Does is_followed_by method work as intended for a false result?"""
        u2 = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
        db.session.add(u2)
        db.session.commit()

        self.assertEqual(self.u.is_followed_by(u2), False)

    def test_signup_successful(self):
        """Does signup class method work as intended given all the correct info is provided?"""
        u2 = User.signup("testuser2", "test2@test.com", "HASHED_PASSWORD2", "https://static.toiimg.com/photo/msid-75390440/75390440.jpg?344550")
        db.session.commit()

        self.assertEqual(u2.__repr__(), f"<User #{u2.id}: testuser2, test2@test.com>")

    def test_signup_fail(self):
        """Does signup class method work as intended if invalid credentials are provided?"""
        try:

            u2 = User.signup("testuser", "test2@test.com", "HASHED_PASSWORD2", "https://static.toiimg.com/photo/msid-75390440/75390440.jpg?344550")
            db.session.commit()

        except IntegrityError:

            self.assertRaises(IntegrityError)

    def test_authenticate_success(self):
        """Does authenticate method work when passing in valid username and password?"""
        u2 = User(email="test2@test.com", username="testuser2", password="HASHED_PASSWORD2")
        db.session.add(u2)
        db.session.commit()

        test = User.authenticate("testuser2", "HASHED_PASSWORD2")

        self.assertEqual(test, u2)