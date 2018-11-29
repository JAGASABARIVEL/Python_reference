#!/usr/bin/env python

"""
This is a reference for the mailing logic with smtp.
"""

import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import datetime
import time
from parsecplogs import Report
import glob

me = "jkarunan@cisco.com"
you = "republic-cruiser@cisco.com"


# Read the XML
cpfile = None
myreport = Report()
for f in glob.glob('/home/Jagasabarivel/Control_Plane_Jobs/cdvr_automation_log/basic-feature_*.log'):cpfile = f
myreport.parse_summary(filename=cpfile)
time.sleep(5)
fail = myreport.total_errors()#0#int(root.attrib.get('failures'))
total = 30#int(root.attrib.get('tests'))
skipped = 0#int(root.attrib.get('skips'))

passed = total - (skipped + fail)

# Create message container - the correct MIME type is multipart/alternative.
msg = MIMEMultipart('alternative')
today = str(datetime.date.today())
if fail != 0:
   s = "Tidel_CP - Daily Run for PPS V3 completed - with ERRORS   "
   subject =  s + today
else:
   s = "Tidel_CP - Daily Run for PPS V3 completed - with SUCCESS   "
   subject = s + today

msg['Subject'] = subject
msg['From'] = me
msg['To'] = you


# Create the body of the message (a plain-text and an HTML version).

text_2 = "\n\nPFA the Report & Log file for today's Control Plane E2E automated suite execution"
text_1 = "Total Test cases ran: %d \nSkipped due to various bugs: %d \n" % (total, skipped)
text_3 = "Passed Test cases: %d \n" % passed
text_4 = "Failed: %d \n" % fail
#text_5 = "Playback warnings - CSCvc25121: %d recordings" % playback_warnings

#text = text_1 + text_3 + text_4 + text_5 + text_2
text = text_1 + text_3 + text_4 + text_2
# Record the MIME types of both parts - text/plain and text/html.
part1 = MIMEText(text, 'plain')


# Attach parts into message container.
# According to RFC 2046, the last part of a multipart message, in this case
# the HTML message, is best and preferred.
msg.attach(part1)


part2 = MIMEBase('application', "octet-stream")
part2.set_payload(open(cpfile, "rb").read())
encoders.encode_base64(part2)
part2.add_header('Content-Disposition', 'attachment; filename="basic-feature.log"')
msg.attach(part2)

# Send the message via local SMTP server.
s = smtplib.SMTP('outbound.cisco.com')
# sendmail function takes 3 arguments: sender's address, recipient's address
# and message to send - here it is sent as one string.
s.sendmail(me, you, msg.as_string())
s.quit()

