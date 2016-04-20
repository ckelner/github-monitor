import boto3

class amazon(object):
  """Provides wrapper for AWS SES.
  """

  SOURCE_EMAIL = 'grid-team@weather.com'

  def __init__(self, aws_access_key_id, aws_secret_access_key, to):
    self.aws_access_key_id = aws_access_key_id
    self.aws_secret_access_key = aws_secret_access_key
    self.to = to.split(',')

  def send(self, subject, body):
    client = boto3.client(
      'ses',
      aws_access_key_id=self.aws_access_key_id,
      aws_secret_access_key=self.aws_secret_access_key
    )

    response = client.send_email(
      Source=self.SOURCE_EMAIL,
      Destination={
        'ToAddresses': self.to
      },
      Message={
        'Subject': {
          'Data': subject
        },
        'Body': {
          'Text': {
            'Data': body
          }
        }
      }
    )

  def sendPublicWhitelist(self, repo_name):
    self.send('Repository ' + repo_name + ' needs to be private', 'Repository '
      + repo_name + ' needs to be Private')
