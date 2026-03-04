from datetime import date, timedelta

from getstream import Stream


def test_query_team_usage_stats_default(client: Stream):
    """Test querying team usage stats with default options."""
    response = client.chat.query_team_usage_stats()
    assert response.data.teams is not None
    assert isinstance(response.data.teams, list)


def test_query_team_usage_stats_with_month(client: Stream):
    """Test querying team usage stats with month parameter."""
    current_month = date.today().strftime("%Y-%m")
    response = client.chat.query_team_usage_stats(month=current_month)
    assert response.data.teams is not None
    assert isinstance(response.data.teams, list)


def test_query_team_usage_stats_with_date_range(client: Stream):
    """Test querying team usage stats with date range."""
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    response = client.chat.query_team_usage_stats(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )
    assert response.data.teams is not None
    assert isinstance(response.data.teams, list)


def test_query_team_usage_stats_with_pagination(client: Stream):
    """Test querying team usage stats with pagination."""
    response = client.chat.query_team_usage_stats(limit=10)
    assert response.data.teams is not None
    assert isinstance(response.data.teams, list)

    # If there's a next cursor, test fetching the next page
    if response.data.next:
        next_response = client.chat.query_team_usage_stats(
            limit=10, next=response.data.next
        )
        assert next_response.data.teams is not None
        assert isinstance(next_response.data.teams, list)


def test_query_team_usage_stats_response_structure(client: Stream):
    """Test that response contains expected metric fields when data exists."""
    end_date = date.today()
    start_date = end_date - timedelta(days=365)
    response = client.chat.query_team_usage_stats(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )

    assert response.data.teams is not None
    teams = response.data.teams

    if teams:
        team = teams[0]
        # Verify team identifier
        assert team.team is not None

        # Verify daily activity metrics
        assert team.users_daily is not None
        assert team.messages_daily is not None
        assert team.translations_daily is not None
        assert team.image_moderations_daily is not None

        # Verify peak metrics
        assert team.concurrent_users is not None
        assert team.concurrent_connections is not None

        # Verify rolling/cumulative metrics
        assert team.users_total is not None
        assert team.users_last_24_hours is not None
        assert team.users_last_30_days is not None
        assert team.users_month_to_date is not None
        assert team.users_engaged_last_30_days is not None
        assert team.users_engaged_month_to_date is not None
        assert team.messages_total is not None
        assert team.messages_last_24_hours is not None
        assert team.messages_last_30_days is not None
        assert team.messages_month_to_date is not None

        # Verify metric structure (each metric has a total field)
        assert team.users_daily.total is not None
