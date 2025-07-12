from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file']

flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret_1020131056840-elv55pg31664fmcef26vaodfv1kdkvam.apps.googleusercontent.com.json',
    scopes=SCOPES
)

creds = flow.run_local_server(port=8080, access_type='offline', prompt='consent')

with open("token_drive.pkl", "wb") as token:
    pickle.dump(creds, token)
