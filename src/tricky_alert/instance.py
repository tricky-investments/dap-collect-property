import json
import smtplib
import ssl

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.audio import MIMEAudio

from email_type import Email
from email_type.receiver import Receiver
from email_type.sender import Sender


class EmailInstance:
    outgoing = []

    def __init__(self, send_from: Sender):
        self.send_from = send_from

    def _send_email(self, recipients: list, email_data: Email):

        # Create message
        message = MIMEMultipart()

        if email_data.links is not None and len(email_data.links) > 0:
            for link in email_data.links:
                email_data.body = email_data.body + '\n\n' + link

        message.attach(MIMEText(email_data.body, 'plain'))
        message['Subject'] = email_data.subject

        # Set email protocol and sign in
        try:
            smtp = smtplib.SMTP(host='smtp.gmail.com', port='587')
            smtp.ehlo()
            smtp.starttls()

            smtp.login(self.send_from.email_address, password=self.send_from.password)

            for r in recipients:
                message['To'] = r.email_address
                message['From'] = self.send_from.email_address
                smtp.sendmail(self.send_from.email_address, r.email_address,  message.as_string())

            smtp.quit()

        except Exception as e:
            # raise e
            print(str(e))
            return False, str(e)

        return True, "Success, emails sent to desired recipients."

    def send_to(self, email_address, email_data: Email):
        pass

    def send_all(self, email_data: Email):
        self._send_email(self.outgoing, email_data=email_data)

    def add_recipients(self, recipients: list):
        self.outgoing.extend(recipients)


if __name__ == '__main__':
    sender = Sender(email_address='trickyinvestments@gmail.com', password='TIpassword4G')
    receiver = Receiver(email_address='troy.fintech@gmail.com', first_name='Troy', last_name='Stanich')
    receiver2 = Receiver(email_address='j.detlet3@yahoo.com', first_name='Jordan', last_name='Detlet')
    receiver3 = Receiver(email_address='ricky.fintech@gmail.com', first_name='Ricky', last_name='Reimers')
    email = Email(subject='Guccy', body='Succy da gooch of da guccy', links=['https://www.marketwatch.com/'])

    instance = EmailInstance(send_from=sender)
    print(instance.send_from.email_address)

    instance.add_recipients([receiver, receiver3])
    instance.send_all(email_data=email)
