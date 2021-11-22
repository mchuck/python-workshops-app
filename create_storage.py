"""
Creates Table storage on Azure in specified resource group.
Usage: python create_storage.py <PREFIX>
"""

import sys
from azure.mgmt.storage import StorageManagementClient
from azure.identity import ClientSecretCredential
from dotenv import set_key, dotenv_values


DOTENV_PATH = '.env'

env = dotenv_values(DOTENV_PATH)

PREFIX = sys.argv[1]

resource_group = 'PythonWorkshop'
account_name = '%sworkshop' % PREFIX.lower()

credential = ClientSecretCredential(
        env['AZURE_TENANT_ID'],
        env['AZURE_CLIENT_ID'],
        env['AZURE_CLIENT_SECRET'])

storage_client = StorageManagementClient(
    credential=credential,
    subscription_id=env['SUBSCRIPTION_ID']
)

storage_account = storage_client.storage_accounts.begin_create(
    resource_group,
    account_name,
    {
        "sku": {
            "name": "Standard_LRS"
        },
        "kind": "StorageV2",
        "location": "westeurope"
    }
).result()

storage_keys = storage_client.storage_accounts.list_keys(
    resource_group_name=resource_group,
    account_name=account_name
)

set_key(DOTENV_PATH, 'STORAGE_NAME', account_name)
set_key(DOTENV_PATH, 'STORAGE_KEY', storage_keys.keys[0].value )

callback_table = storage_client.table.create(
    resource_group,
    account_name,
    'callbacks'
)

log_table = storage_client.table.create(
    resource_group,
    account_name,
    'logs'
)
