from users.helpers import create_test_users


def create_tvseries(users):

    tv_series_data = dict(
        entry_author=users[0],
        name='Django unleashed', 
    )