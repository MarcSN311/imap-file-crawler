# IMAP File Crawler

I made this to crawl all the PDF files from my IMAP inbox. You can write custom "validators" if you are not looking for PDFs.

## Usage

`get_files_from_imap.py -h` has (almost) all the info you will need

### Configuration file

`get_files_from_imap.py cfg` will download files based on `config.ini`

look at `get_files_from_imap.py cfg -h` for more info 

### Shell

`get_files_from_imap.py cli <hostname> <username> <password>` will download all attachments ending in ".pdf" to /tmp 

look at `get_files_from_imap.py cli -h` for more info 
