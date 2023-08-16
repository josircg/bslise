import smtplib, ssl
from eucs_platform import send_email
from django.conf import settings


def bare_test():
    port = 587  # For starttls
    smtp_server = "smtp.apps.ibict.br"
    sender_email = "xxxx@apps.ibict.br"
    receiver_email = "josircg@gmail.com"
    password = input("Type your password and press enter:")
    message = """\
    Subject: Teste Python"""

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


def django_email():
    print(f'Sending to {settings.ADMINS}')
    send_email( 'Teste', 'Test email', settings.ADMINS)


django_email()
print('Message sent!')
