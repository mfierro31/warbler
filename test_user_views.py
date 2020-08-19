"""User views tests."""

# run these tests like:
#
#    python -m unittest test_user_views.py


import os
from unittest import TestCase
from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# To stop WTForms from enforcing the CSRF token

app.config['WTF_CSRF_ENABLED'] = False

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

        db.session.add_all([self.u, self.u2])
        db.session.commit()

        self.client = app.test_client()

        # For some reason, if we try to access self.u.id or self.u2.id in the test functions below
        # while also using .session_transaction(), it will give us an error saying that self.u and self.u2 are
        # 'detached' from the session, so instead, we have to pull their id's out and place them into their
        # own variables.
        self.u_id = self.u.id
        self.u2_id = self.u2.id
        self.m_id = self.m.id
        self.m2_id = self.m2.id

    def tearDown(self):
        """Remove any fouled transactions"""
        db.session.rollback()

    def test_logged_in_followers_following_pages(self):
        """If you're logged in, can you see another user's followers and following pages?"""
        with self.client.session_transaction() as change_session:
            change_session['curr_user'] = self.u_id

        resp = self.client.get(f"/users/{self.u2.id}/followers")
        html = resp.get_data(as_text=True)

        resp2 = self.client.get(f"/users/{self.u2.id}/following")
        html2 = resp2.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<p>@testuser</p>', html)

        self.assertEqual(resp2.status_code, 200)
        self.assertIn('<p>@testuser</p>', html2)

    def test_logged_out_followers_following_pages(self):
        """If you're logged out, are you not allowed to see a user's followers and following pages?"""
        
        resp = self.client.get(f"/users/{self.u2.id}/followers", follow_redirects=True)
        html = resp.get_data(as_text=True)

        resp2 = self.client.get(f"/users/{self.u2.id}/following", follow_redirects=True)
        html2 = resp2.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<h4>New to Warbler?</h4>', html)

        self.assertEqual(resp2.status_code, 200)
        self.assertIn('<h4>New to Warbler?</h4>', html2)

    def test_add_message_as_self(self):
        """If you're logged in, can you add a message as yourself?"""
        with self.client.session_transaction() as change_session:
            change_session['curr_user'] = self.u_id

        resp = self.client.post("/messages/new", data={'text': 'New message!'}, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<p>New message!</p>', html)

    def test_delete_message_as_self(self):
        """If you're logged in, can you delete a message as yourself?"""
        with self.client.session_transaction() as change_session:
            change_session['curr_user'] = self.u_id

        resp = self.client.post(f"/messages/{self.m_id}/delete", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn(f'<a href="/users/{self.u_id}">0</a>', html)

    def test_logged_out_add_message(self):
        """If you're logged out, are you allowed to add a message?"""
        resp = self.client.post("/messages/new", data={'text': 'New message!'}, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("<h1>What's Happening?</h1>", html)

    def test_logged_out_delete_message(self):
        """If you're logged out, are you allowed to delete a message?"""
        resp = self.client.post(f"/messages/{self.m_id}/delete", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

    def test_add_message_as_different_user(self):
        """If you're logged in, can you add a message as another user?"""
        # There's no good way to test this, because the way the route is set up, there's no way to check who's adding the
        # message.  It's just always going to be whoever is logged in.  So, instead, we can just test if we add a message
        # as 2 different users, do those messages stay associated with their correct user?
        with self.client.session_transaction() as change_session:
            change_session['curr_user'] = self.u_id

        resp = self.client.post("/messages/new", data={'text': 'New message!'}, follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<p>New message!</p>', html)

        with self.client.session_transaction() as change_session:
            change_session['curr_user'] = self.u2_id

        resp2 = self.client.post("/messages/new", data={'text': 'New message 2!'}, follow_redirects=True)
        html2 = resp2.get_data(as_text=True)

        self.assertEqual(resp2.status_code, 200)
        self.assertIn('<p>New message 2!</p>', html2)
        
    def test_delete_message_as_different_user(self):
        """If you're logged in, can you delete another user's messages?"""
        with self.client.session_transaction() as change_session:
            change_session['curr_user'] = self.u_id

        resp = self.client.post(f"/messages/{self.m2_id}/delete", follow_redirects=True)
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)