import imaplib
import configparser
import os
import email.header
import logging
from tqdm import tqdm
from argh import *
from pprint import pprint

class imap_file_crawler():
  def __init__(self, hostname, username, password, download_folder, port=993, loglevel="WARNING"):
    logging.basicConfig(level=loglevel)
    self.hostname = hostname
    self.port = port
    self.username = username
    self.password = password
    self.download_folder = download_folder

  def connect(self):
    logging.info(f"Connecting to {self.hostname}")
    connection = imaplib.IMAP4_SSL(self.hostname, port=self.port)

    logging.info(f"Logging in as {self.username}")
    connection.login(self.username, self.password)
    self.connection = connection

  def disconnect(self):
    if 'connection' in dir(self):
      self.connection.logout()

  @staticmethod
  def trueValidator(dummy):
    return True

  def crawl(self, folder='INBOX', imap_filter='ALL', validator=True):
    self.connection.select(folder, readonly=self.trueValidator)
    typ, msg_ids = self.connection.search(None, imap_filter)
    for id in tqdm(msg_ids[0].split()):
      try:
        result, email_data = self.connection.fetch(id, '(RFC822)')
        if email_data[0] is None:
          logging.warning(f"{id} is None, result was: {result}")
          continue
        email_message = email.message_from_bytes(email_data[0][1])
        for part in email_message.walk():
          if part.get_content_maintype() == 'multipart':
            logging.debug("skipped multipart")
            continue
          if part.get('Content-Disposition') is None:
            logging.debug("skipped Content-Disposition=None")
            continue
          if part.get('Content-Disposition') == "inline":
            logging.debug("skipped Content-Disposition=inline")
            continue
          filename = part.get_filename()
          if filename is None:
            if self.verbose: pprint(part.items())
            continue
          if validator(filename):
            att_path = os.path.join(self.download_folder, filename)
            if not os.path.isfile(att_path):
              fp = open(att_path, 'wb')
              fp.write(part.get_payload(decode=True))
              fp.close()
      except Exception as e:
        if 'email_data' in locals():
          pprint(email_data)
        self.disconnect()
        raise

# example validator that check if file has ".pdf" extension
def isPDF(filename):
  return filename.endswith(".pdf")

@named('cli')
@arg('-v', '--verbosity', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
def run(hostname : "Mailserver hostname", username : "Mail account username", 
        password : "Mail account password", 
        download_folder : "Folder to which the files will be downloaded" = "/tmp", 
        port : "Mailserver SSL port" = 993, 
        folder : "The imap folder you want to crawl" = "INBOX",
        verbosity : "Changes output verbosity" = "WARNING"):
  '''
  run with parameters supplied to command
  '''
  try:
    crawler = imap_file_crawler(hostname, username, password, download_folder, port, verbosity)
    crawler.connect()
    crawler.crawl(folder=folder, validator=isPDF)
  finally:
    crawler.disconnect()

@named('config')
@aliases('cfg')
@arg('-v', '--verbosity', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
def run_with_configfile(configfile : "Config file in ini format" = "config.ini", 
                        verbosity : "Changes output verbosity" = ""):
  '''
  run with parameters from config file
  '''
  config = configparser.ConfigParser()
  config.read(configfile)

  if not verbosity:
    verbosity = config.get('general', 'verbose', fallback="WARNING")
  hostname = config.get('server', 'hostname')
  port = config.get('server', 'port', fallback='993')
  username = config.get('account', 'username')
  password = config.get('account', 'password')
  imap_folder = config.get('account', 'folder', fallback='INBOX')
  download_folder = config.get('download', 'folder', fallback='/tmp')

  run(hostname, username, password, download_folder, port, imap_folder, verbosity)

if __name__ == '__main__':
  p = ArghParser()
  p.add_commands([run_with_configfile, run])
  dispatch(p)
