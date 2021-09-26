from lib.abstract import Task

import tricky_alert
from tricky_alert import email_type


class ProcessPropertiesTask(Task):

    TASK_NAME = "Property Process Task"

    def __str__(self):
        return self.TASK_NAME

    def load_settings(self, settings):
        self.tricky_alert_config = settings['tricky_alert_config']

    def load_parameters(self, params):

        for key in params.keys():
            if key == 'properties':
                continue
            for key2 in params[key].keys():
                params[key][key2] = str(params[key][key2])

        self.content = params

    def run(self):

        success = True

        """
        INITIALIZE EMAIL SENDER, RECIPIENTS, AND EMAIL INSTANCE
        """
        receivers = []
        for email in self.tricky_alert_config['receiver_emails']:
            receiver = email_type.receiver.Receiver(email, 'TODO', 'TODO')
            receivers.append(receiver)

        sender = email_type.sender.Sender(self.tricky_alert_config['sender_email'], self.tricky_alert_config['sender_pass'])
        instance = tricky_alert.instance.EmailInstance(send_from=sender)
        instance.add_recipients(receivers)

        print(self.content)

        for prop in self.content['properties']:

            subject = f"Property Found in {self.content['area_data']['City']}"

            body = f"Property Found in {self.content['area_data']['City']}, {self.content['area_data']['State']}.\n\n"

            body += "Area Data:\n"
            for key in self.content['area_data'].keys():
                body += f"\t{key}:   {self.content['area_data'][key]}\n"

            body += "\nMortgage Data:\n"
            for key in self.content['mortgage_params'].keys():
                body += f"\t{key}:   {self.content['mortgage_params'][key]}\n"

            body += "\nEstimated Expenses:\n"
            for key in self.content['expected_expenses'].keys():
                body += f"\t{key}:   {self.content['expected_expenses'][key]}\n"

            body += "\nRequired KPI's:\n"
            for key in self.content['required_kpis'].keys():
                body += f"\t{key}:   {self.content['required_kpis'][key]}\n"

            body += "\nProperty Information:\n"
            for key in prop.keys():
                if key == 'link':
                    continue
                body += f"\t{key}:   {prop[key]}\n"

            email = email_type.Email(subject=subject, body=body, links=[prop['link']])
            instance.send_all(email)

        return success, 'SUCCESS'
