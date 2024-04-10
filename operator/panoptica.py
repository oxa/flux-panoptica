import kopf
import logging
import requests
import os
import yaml
import kubernetes

@kopf.on.create('panopticaaccounts')
def create_fn(spec, name, namespace, logger, **kwargs):
    integration_id = spec.get('integrationId')
    api_key = spec.get('apiKey')
    if not integration_id:
        raise kopf.PermanentError(f"integrationId must be set. Got {integration_id!r}.")
    if not api_key:
        raise kopf.PermanentError(f"apiKey must be set. Got {api_key!r}.")
    
    url = f"https://api.us1.console.panoptica.app/api/kis/integrations/{integration_id}"
    
    headers = {
        "accept": "text/plain",
        "Authorization": api_key
    }

    response = requests.get(url, headers=headers)

    path = os.path.join(os.path.dirname(__file__), 'secrets.yaml')
    tmpl = open(path, 'rt').read()
    text = tmpl.format(name=name, size=response.text)
    data = yaml.safe_load(text)
    
    kopf.adopt(data)

    api = kubernetes.client.CoreV1Api()
    obj = api.create_namespaced_config_map(namespace=namespace, body=data)
    
    logger.info(f"Panoptica configmap is created: {obj}")
    return {'pca-name': obj.metadata.name}


