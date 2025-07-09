from httpx import Client
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from time import sleep
from sys import argv, exit

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
    'Cookie':''
    }

websites = {
    'linkjust.com':{
        'referer':'https://forexrw7.com/',
        'second_url': 'https://linkjust.com/links/go',
        'delay':5
    }
}

def http2(url, method='GET', headers={}, data=None, params=None, json=None, timeout=30):
    try:
        params = params or {}

        with Client(http2=True, verify=False, timeout=timeout) as client:
            response = client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=json,
                data=data if not isinstance(data, dict) else None,
                params=params,
            )

            try:
                ip_address = response.ext['network_stream'].get_extra_info('peername')[0]
            except Exception:   
                ip_address = None  # Handle cases where IP extraction fails
            # Determine response body based on content type
            content_type = response.headers.get('Content-Type', '')
            if 'text' in content_type:
                res_body = response.text
            elif 'json' in content_type:
                res_body = response.json()
            else:
                res_body = response.text

            # Return structured response
            return {
                'ip':ip_address,
                'status_code': response.status_code,
                'request_headers': response.request.headers,
                'response_headers': response.headers,
                'response_body': res_body,
            }

    except Exception as e:
        print(e)
        return False

def get_host(url):
    return url.split('//')[1].split('/')[0]

def first_request(url, host):
    global headers
    headers['Referer']= websites[get_host(url)]['referer']
    print(f'\n[+] Sending First Request ...')
    response = http2(url, headers=headers)
    try:
        status_code = response['status_code']
        if status_code == 200:
            cookies = [value for (key, value) in response['response_headers'].items() if key.lower() == 'set-cookie'][0]
            headers['Cookie'] += f"AppSession={cookies.split('AppSession=')[1].split(';')[0]}; "
            csrf_token = cookies.split('csrfToken=')[1].split(';')[0]
            headers['Cookie'] += f"csrfToken={csrf_token}; "
            end_point = f"ref{url.split('/')[-1]}"
            headers['Cookie'] += f"{end_point}={cookies.split(f'{end_point}=')[1].split(';')[0]}; "

            soup = BeautifulSoup(response['response_body'], 'html.parser')
            input_tag = soup.find('input', {'name': 'ad_form_data'})
            if input_tag: ad_form_data = input_tag.get('value')
            input_tag = soup.find('input', {'name': '_Token[fields]'})
            if input_tag: token_field = input_tag.get('value')

            print('[=] Done\n')
            return {
                'csrf_token': csrf_token,
                'ad_form_data': ad_form_data,
                'token_field': token_field
            }
        else:
            print(f'[=] Error: status code {status_code}\n')
            return []
    except Exception as e:
        print(f'[=] Error: {e}\n')
        return []


def second_request(data):
    global headers
    url = 'https://linkjust.com/links/go'
    headers['Content-Type'] = "application/x-www-form-urlencoded; charset=UTF-8"
    headers['X-Requested-With'] = "XMLHttpRequest"
    data = {
        "_method":"POST",
        '_csrfToken': data['csrf_token'],
        "ad_form_data": data['ad_form_data'],
        "_Token[fields]": data['token_field'],
        "_Token[unlocked]": "adcopy_challenge|adcopy_response|g-recaptcha-response|h-captcha-response"
    }


    print('[+] Sending Second Request ...')
    response = http2(url, method='POST', headers=headers, data=urlencode(data))
    
    if response:
        try:
            print(f"[=] Link: {response['response_body']['url']}\n")
        except Exception as e:
            print(f'[=] Error: {e}')
            

def bypasser(url):
    host = get_host(url)
    data = first_request(url, host)
    if data:
        delay = websites[host]['delay']
        print(f'[+] Sleep {delay} sec')
        sleep(delay)
        second_request(data)

if __name__ == "__main__":
    if len(argv) == 1: 
        print('\n## Requirements: pip install httpx beautifulsoup4')
        print("## Usage: python short_link_bypasser.py https://linkjust.com/1KEvtFiwr")
        exit()
    url = argv[1]
    bypasser(url)

