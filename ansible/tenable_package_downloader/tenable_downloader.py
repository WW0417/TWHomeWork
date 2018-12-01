#!/usr/bin/env python3
import requests, configparser, sys, getopt, signal, time
from bs4 import BeautifulSoup

#timeout handling
#generate an sub-class from class Exception
class TimeOut(RuntimeError):
    pass
def signal_handler(signum, frame):
    raise TimeOut('Time out.')

#for debug
proxy = {"http":"http://127.0.0.1:8080", "https":"http://127.0.0.1:8080"}


#use beautifusoup to parse the Tenable download page to get the data-download-id, data-page-id, and csrf-token, which are needed for downloading from Tenable's S3 buckets
def parse(session, pkg_name):
    #"soup" is a BeautifulSoup object
    soup = BeautifulSoup(session.text, 'html.parser')
    #"find" function returns a tag object
    download_link = soup.find(attrs={"data-file-name": pkg_name})
    csrf_token = soup.find(attrs={"name": 'csrf-token'})
    #print(csrf_token.attrs['content'])
    return download_link.attrs['data-download-id'], download_link.attrs['data-page-id'], csrf_token.attrs['content']


def download(url_download_page, pkg_name):
    session = requests.Session()

    #get_info = session.get(url_download_page, proxies = proxy, verify=False)
    get_info = session.get(url_download_page)

    parse_result = parse(get_info, pkg_name)
    #print(parse_result)
    download_id = parse_result[0]
    page_id = parse_result[1]
    csrf_token = parse_result[2]
    url_post = 'https://www.tenable.com/downloads/pages/' + page_id + '/downloads/' + download_id + '/download_file'
    #the csrf_token needs to be URL-encoded, thus post_payload must be a dict for the post method, not a string
    post_payload = {'_method': 'get_download_file', 'i_agree_to_tenable_license_agreement': 'true', 'commit': 'I+Agree', 'authenticity_token': csrf_token}
    #print(post_payload, url_post)

    redirect_page = session.post(url_post, data = post_payload, allow_redirects=False)
    #redirect_page = session.post(url_post, data = post_payload, proxies = proxy, verify=False)

    #print(redirect_page.status_code, redirect_page.headers['Location'])
    print('Target package URL is:\n' + redirect_page.headers['Location'] + '\n')
    package = requests.get(redirect_page.headers['Location'], stream=True)
    try:
        filelen = package.headers['content-length']
    except KeyError:
        print('Error: No content-length header in response. Maybe the package name is wrong?\n')
    else:
        if int(filelen) < 1000000:
            print('Error: Expected file length is only', filelen, 'bytes. Maybe the package name is wrong?\n')
        else:
            print('Expected file length is', filelen,
            'bytes.\nStart downloading...\n')
            with open(pkg_name, 'wb') as dstfile:
                dstfile.write(package.content)


def main(argv):

    #Tenable download page
    url_sc = 'https://www.tenable.com/downloads/securitycenter-3d-tool-and-xtool'
    url_nessus = 'https://www.tenable.com/downloads/nessus'

    try:
        opts, args = getopt.getopt(argv, "", ['nessus', 'sc'])
    except getopt.GetoptError:
        print(usage_guide)
        sys.exit()
    if len(args) >= 1:
        print(usage_guide)
        sys.exit()
    elif len(opts) >= 2:
        print(usage_guide)
        sys.exit()
    elif opts[0][0] == "--nessus":
        try:
            conf=configparser.ConfigParser()
            conf.read('./downloader.conf')
            pkg_name = conf.get('package name', 'Nessus_package')
            download(url_nessus, pkg_name)
        except configparser.NoSectionError:
            print('Failed to read configuration file.\n')
            sys.exit()
    elif opts[0][0] == "--sc":
        try:
            conf=configparser.ConfigParser()
            conf.read('./downloader.conf')
            pkg_name = conf.get('package name', 'SC_package')
            download(url_sc, pkg_name)
        except configparser.NoSectionError:
            print('Failed to read configuration file.\n')
            sys.exit()
    else:
        print('Unexpected error.\n')
        sys.exit()


if __name__ == "__main__":

    usage_guide = 'Usage:\n Download Nessus package:               /tenable_downloader.py --nessus\n Download SecurityCenter package:       /tenable_downloader.py --sc\n'

    if len(sys.argv) == 1:
        print(usage_guide)
        sys.exit()

    #set timeout counter to 600 seconds
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(600)

    try:
        main(sys.argv[1:])
    except TimeOut:
        print('Connection time out.\n')
        sys.exit()
    except requests.exceptions.ConnectionError:
        print('Connection error. Check the reachability to the server.\n')
        sys.exit()
