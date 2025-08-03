import pytest
import datetime
from app.main import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_health_check(client):
    res = client.get('/')
    assert res.status_code == 200
    assert res.get_json()['status'] == 'healthy'

def test_shorten_and_redirect(client):
    res = client.post('/api/shorten', json={'url': 'https://example.com'})
    assert res.status_code == 201
    data = res.get_json()
    assert 'short_code' in data
    assert 'short_url' in data

    short_code = data['short_code']
    redirect_res = client.get(f'/{short_code}', follow_redirects=False)
    assert redirect_res.status_code == 302
    assert redirect_res.headers['Location'] == 'https://example.com'

def test_invalid_url(client):
    res = client.post('/api/shorten', json={'url': 'invalid-url'})
    assert res.status_code == 400
    assert 'error' in res.get_json()

def test_empty_url(client):
    res = client.post('/api/shorten', json={'url': ''})
    assert res.status_code == 400
    assert 'error' in res.get_json()

def test_missing_url(client):
    res = client.post('/api/shorten', json={})
    assert res.status_code == 400
    assert 'error' in res.get_json()

def test_stats(client):
    res = client.post('/api/shorten', json={'url': 'https://example.com'})
    short_code = res.get_json()['short_code']

    # Trigger click
    client.get(f'/{short_code}')

    stats_res = client.get(f'/api/stats/{short_code}')
    stats = stats_res.get_json()

    assert stats_res.status_code == 200
    assert stats['clicks'] >= 1
    assert stats['url'] == 'https://example.com'

    # Check timestamp format
    datetime.datetime.strptime(stats['created_at'], "%Y-%m-%dT%H:%M:%S")

def test_click_count_increment(client):
    res = client.post('/api/shorten', json={'url': 'https://example.com'})
    short_code = res.get_json()['short_code']

    client.get(f'/{short_code}')
    client.get(f'/{short_code}')

    stats = client.get(f'/api/stats/{short_code}').get_json()
    assert stats['clicks'] == 2

def test_different_codes_for_same_url(client):
    res1 = client.post('/api/shorten', json={'url': 'https://example.com'})
    res2 = client.post('/api/shorten', json={'url': 'https://example.com'})
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.get_json()['short_code'] != res2.get_json()['short_code']

def test_redirect_invalid_short_code(client):
    res = client.get('/invalid123')
    assert res.status_code == 404

def test_stats_invalid_short_code(client):
    res = client.get('/api/stats/invalid123')
    assert res.status_code == 404
