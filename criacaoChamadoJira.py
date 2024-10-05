from atlassian import Jira
from requests import HTTPError

jira = Jira(
    url = "https://vault-wise.atlassian.net", #URL DA EMPRESA
    username = "nicolas.lopes@sptech.school", #EMAIL
    password = "" #TOKEN
)

try:

    jira.issue_create(
        fields={
            'project': {
                'key': 'VAULT' #SIGLA DO PROJETO
            },
            'summary': 'Alerta de CPU',
            'description': 'CPU acima da média',
            'issuetype': {
                "name": "Task"
            },
    
        }
    )
except HTTPError as e:
    print(e.response.text)