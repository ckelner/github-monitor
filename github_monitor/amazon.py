import boto3

class Amazon(object):
  """
  AWS SES client using boto3.
  """

  def __init__(self, aws_access_key_id, aws_secret_access_key, destination_emails,
    source_email, subject=None, body=None):
    self.aws_access_key_id = aws_access_key_id
    self.aws_secret_access_key = aws_secret_access_key
    self.source_email = source_email
    self.destination_emails = destination_emails.split(',')
    self.subject = subject
    self.body = body

    self.client = boto3.client(
      'ses',
      aws_access_key_id=self.aws_access_key_id,
      aws_secret_access_key=self.aws_secret_access_key
    )

  def send(self, subject, body):
    if body is None or subject is None:
      print 'Email not sent: body and subject must be defined'
      return

    self.client.send_email(
      Source=self.source_email,
      Destination={
        'ToAddresses': self.destination_emails
      },
      Message={
        'Subject': {
          'Data': self.subject
        },
        'Body': {
          'Text': {
            'Data': self.body
          }
        }
      }
    )
