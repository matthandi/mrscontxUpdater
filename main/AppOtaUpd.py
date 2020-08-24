"""
AppOtaUpd - over-the-air updater for the App(s)
"""
import urequests
import ujson
import network
import time
import os
import gc
import machine

class CAppOtaUpd:
    """
    class for over-the-air file updater
    """
    def __init__(self,github_repo, module='', main_dir='main',user_agent="awesome-app"):
        """
        constructor:
        - User-Agent is necessary for accessing github.com
        """
        super().__init__()
        self.github_repo = github_repo.rstrip('/').replace('https://github.com', 'https://api.github.com/repos')
        self.main_dir = main_dir
        self.module = module.rstrip('/')
        self.user_agent = {'User-Agent': user_agent }

    def read_configfile(self):
        with open('ssid.json') as f:
            self.ssid_data = ujson.load(f)
        self.ssid_wlan = self.ssid_data['SSIDS'][0]['ssid']
        self.key_wlan = self.ssid_data['SSIDS'][0]['key']
    
    @staticmethod
    def using_network(ssid, password):
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
            print('connecting to network...')
            sta_if.active(True)
            sta_if.connect(ssid, password)
            while not sta_if.isconnected():
                time.sleep(0.1)
        print('network config:', sta_if.ifconfig())

    def get_version(self, directory, version_file_name='.version'):
        """
        get local version of versionfile
        """
        try:
            if version_file_name in os.listdir(directory):
                f = open(directory + '/' + version_file_name)
                version = f.read()
                f.close()
                return version
            else:
                return '0.0'
        except OSError:
            return '0'

    def get_latest_release_version(self):
        """
        retrieve the latest release version from github.com
        """
        try:
            latest_release = urequests.get(self.github_repo + '/releases/latest',headers=self.user_agent)
            version = latest_release.json()['tag_name']
            latest_release.close()
            return version
        except (IndexError,KeyError,OSError,TypeError,ValueError):
            return "[E] reading latest version"

    def rmtree(self, directory):
        """
        removes a complete directory with all subdirectories
        """
        for entry in os.ilistdir(directory):
            is_dir = entry[1] == 0x4000
            if is_dir:
                self.rmtree(directory + '/' + entry[0])

            else:
                os.remove(directory + '/' + entry[0])
        os.rmdir(directory)

    def download_updates_if_available(self):
        """
        downloads an update if available to local directory without installing it
        """
        current_version = self.get_version(self.modulepath(self.main_dir))
        latest_version = self.get_latest_release_version()

        print('Checking version... ')
        print('\tCurrent version: ', current_version)
        print('\tLatest version : ', latest_version)
        if latest_version > current_version:
            print('Updating...')
            try:
                os.mkdir(self.modulepath('next'))
            except OSError:
                pass
            self.download_all_files(self.github_repo + '/contents/' + self.main_dir, latest_version)
            with open(self.modulepath('next/.version'), 'w') as versionfile:
                versionfile.write(latest_version)
                versionfile.close()

            return True
        return False


    def download_all_files(self, root_url, version):
        file_list = urequests.get(root_url + '?ref=' + version,headers=self.user_agent)
        for file in file_list.json():
            if file['type'] == 'file':
                download_url = file['download_url']
                download_path = self.modulepath('next/' + file['path'].replace(self.main_dir + '/', ''))
                self.download_file(download_url, download_path)
            elif file['type'] == 'dir':
                path = self.modulepath('next/' + file['path'].replace(self.main_dir + '/', ''))
                os.mkdir(path)
                self.download_all_files(root_url + '/' + file['name'], version)

        file_list.close()

    def download_file(self, url, path):
        print('\tDownloading: ', path)
        with open(path, 'w') as outfile:
            try:
                response = urequests.get(url,headers=self.user_agent)
                outfile.write(response.text)
            finally:
                response.close()
                outfile.close()
                gc.collect()

    def modulepath(self, path):
        return self.module + '/' + path if self.module else path

    def install_files(self):
        """
        new files are available in next
        versions from main and next are different
        """
        upd_version = self.get_version("next")
        # update available
        if upd_version > '0.0':
            #remove existing prev
            try:
                self.rmtree("prev")
                print("prev directory removed")
            except OSError:
                print("no prev directory exists...")

            #rename existing main -> prev
            try:
                os.rename(self.main_dir,"prev")
            except OSError:
                print("INFO:" + self.main_dir + " doesn't exist")

            #rename next -> main
            try:
                os.rename("next",self.main_dir)
            except OSError:
                print("Error: unable to rename next -> main_dir")
                return False
            #reboot :)
            machine.reset()
            return True

        else:
            print("no update available to install")
            return False

if __name__ == "__main__":
    o = CAppOtaUpd("https://github.com/matthandi/mrscontxUpdater")
    print(o.get_version(o.modulepath(o.main_dir)))
    print(o.get_latest_release_version())
    o.download_updates_if_available()
    o.install_files()
    