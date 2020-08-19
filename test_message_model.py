"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy.exc import IntegrityError
from models import db, User, Message

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


class MessageModelTestCase(TestCase):
    """Test message model."""
    def setUp(self):
        """Set up a user and a message for them"""
        User.query.delete()
        Message.query.delete()

        self.u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(self.u)
        db.session.commit()

        self.m = Message(text="Testing!", user_id=self.u.id)
        db.session.add(self.m)
        db.session.commit()

    def tearDown(self):
        """Remove any fouled transactions"""
        db.session.rollback()

    def test_message_model(self):
        """Does basic Message model work?"""
        self.assertEqual(self.m.id, self.m.id)
        self.assertEqual(self.m.text, "Testing!")
        self.assertEqual(self.m.timestamp, self.m.timestamp)
        self.assertEqual(self.m.user_id, self.u.id)
        self.assertEqual(self.m.user, self.u)

    def test_create_message(self):
        """Can we successfully create a new message using the correct data?"""
        m2 = Message(text="Testing twice!", user_id=self.u.id)
        db.session.add(m2)
        db.session.commit()

        self.assertEqual(m2.text, "Testing twice!")

        try:
            m3 = Message(text="Testing thrice!")
            db.session.add(m3)
            db.session.commit()
        except IntegrityError:
            self.assertRaises(IntegrityError)

    def test_on_delete_cascade(self):
        """Will message be deleted if associated user is deleted?"""
        db.session.delete(self.u)
        db.session.commit()

        self.assertIsNone(Message.query.filter_by(id=self.m.id).one_or_none())