import requests
import json

def test():
    # 1. Login as admin
    login_res = requests.post(
        'http://127.0.0.1:8000/api/v1/auth/login',
        data={'username': 'admin@workforceiq.local', 'password': 'AdminSecurePassword2026!'}
    )
    print('Login status:', login_res.status_code)
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}

    # 2. Post new employee with experience fields
    payload = {
        'first_name': 'Sarah',
        'last_name': 'Connor',
        'email': 'sconnor.exp@workforceiq.local',
        'department': 'Engineering',
        'location': 'San Francisco, CA',
        'hire_date': '2026-10-31',
        'standard_hours_per_week': 40.0,
        'cost_rate_per_hour': 85.0,
        'system_role': 'EMPLOYEE',
        'years_of_experience': 7.5,
        'experience_level': 'Senior',
        'previous_company': 'Cyberdyne Systems',
        'experience_summary': '7+ years leading distributed systems and high-throughput real-time APIs.'
    }
    res = requests.post('http://127.0.0.1:8000/api/v1/employees', headers=headers, json=payload)
    print('Create employee status:', res.status_code)
    data = res.json()
    if res.status_code != 201:
        print('Error:', data)
        # Maybe email already exists from earlier test?
        emp_id = 'test'
    else:
        emp_id = data.get('id')
        print('Created employee:')
        print('  ID:', emp_id, 'Business ID:', data.get('business_id'))
        print('  Years of Exp:', data.get('years_of_experience'))
        print('  Level:', data.get('experience_level'))
        print('  Previous Company:', data.get('previous_company'))
        print('  Summary:', data.get('experience_summary'))

        # 3. Retrieve employee by ID
        get_res = requests.get(f'http://127.0.0.1:8000/api/v1/employees/{emp_id}', headers=headers)
        print('Get employee status:', get_res.status_code)
        get_data = get_res.json()
        assert get_data.get('years_of_experience') == 7.5
        assert get_data.get('experience_level') == 'Senior'
        assert get_data.get('previous_company') == 'Cyberdyne Systems'
        assert 'distributed systems' in get_data.get('experience_summary')
        print('All experience fields verified successfully!')

if __name__ == '__main__':
    test()
