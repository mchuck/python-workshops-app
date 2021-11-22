""" Application logic for managing callbacks """

import io
import os
import uuid
from collections import Counter
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from azure.data.tables import TableServiceClient


def _create_service_client():
    return TableServiceClient.from_connection_string(os.environ['CONNECTION_STRING'])


def _azure_time_to_datetime(azure_time):
    return datetime(
        azure_time.year,
        azure_time.month,
        azure_time.day,
        azure_time.hour,
        azure_time.minute
    )


def create_callback(display_name):
    guid = uuid.uuid4()

    with _create_service_client() as service_client:
        table_client = service_client.get_table_client('callbacks')
        table_client.upsert_entity(
            {'PartitionKey': 'callback', 'RowKey': guid, 'DisplayName': display_name}
        )

    return guid


def rename_callback(callback_id, new_name):
    with _create_service_client() as service_client:
        table_client = service_client.get_table_client('callbacks')
        entity = table_client.get_entity(
            partition_key='callback',
            row_key=callback_id)
        entity['DisplayName'] = new_name
        table_client.update_entity(entity)


def delete_callback(callback_id):
    with _create_service_client() as service_client:
        table_client = service_client.get_table_client('callbacks')
        table_client.delete_entity(
            partition_key='callback',
            row_key=callback_id
        )


def process_call(callback_id, status):
    log_id = uuid.uuid4()

    with _create_service_client() as service_client:
        table_client = service_client.get_table_client('logs')
        table_client.upsert_entity({
            'PartitionKey': callback_id,
            'RowKey': log_id,
            'Status': status,
            'Created': datetime.now()
        })

    return log_id


def generate_image(callback_id):

    # query logs from last 20 minutes
    current_time = datetime.utcnow()
    filter_time = current_time - timedelta(minutes=20)
    filter_time = filter_time.replace(second=0, microsecond=0)

    with _create_service_client() as service_client:
        table_client = service_client.get_table_client('logs')
        logs = table_client.query_entities(
            "PartitionKey eq @callbackId and Created gt datetime'%s'" % filter_time.isoformat(),
            select=['Created', 'Status'],
            parameters={'callbackId': callback_id}
        )

        logs = list(logs)   # fetch all matching logs

    # convert data to format appropiate for plotting
    logs = [(_azure_time_to_datetime(x['Created']), x['Status']) for x in logs]
    
    plot_data = {}
    plot_data['time'] = [
        (current_time - timedelta(minutes=i)).replace(second=0, microsecond=0) \
            for i in reversed(range(0, 21))
    ]

    statuses = {x[1] for x in logs}
    for s in statuses:
        plot_data[s] = []

    for t in plot_data['time']:
        span = [x[1] for x in logs if x[0] == t]
        counter = Counter({s : 0 for s in statuses})
        counter.update(span)

        for status, c in counter.most_common():
            plot_data[status].append(c)

    # draw and style plot
    sns.set()
    _, ax = plt.subplots()

    for s in statuses:
        sns.lineplot(x='time', y=s, data=plot_data, label=s)
    
    ax.set_ylabel("Count")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    buf = io.BytesIO()
    plt.savefig(buf, format='png')

    return buf.getvalue()


def get_callback_info(callback_id):
    print(callback_id)
    with _create_service_client() as service_client:
        table_client = service_client.get_table_client('callbacks')
        entity = table_client.get_entity(
            partition_key='callback',
            row_key=callback_id)

    return { 'id': callback_id, 'display_name': entity['DisplayName'] }
