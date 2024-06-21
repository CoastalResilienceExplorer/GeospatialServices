from google.cloud import datastore
from datetime import datetime
from uuid import uuid4

client = datastore.Client(project="global-mangroves", database="managed-assets")

def add_entity(entity_type, info):
    # Create a Key object for the entity
    id = str(uuid4())
    entity_key = client.key(entity_type, id)

    # Define the entity properties
    entity = datastore.Entity(key=entity_key)
    for k, v in info.items():
        entity[k] = v
    entity['created_at'] = datetime.now()
    
    client.put(entity)

def entity_to_json(entity):
    entity_json = {}
    for key, value in entity.items():
        if isinstance(value, datetime):
            entity_json[key] = value.isoformat()
        else:
            entity_json[key] = value
    entity_json['id'] = entity.key.id_or_name
    return entity_json


def get_managed_assets(entity_type):
    # Create a Key object for the entity
    entities = list(client.query(kind=entity_type).fetch())
    entities_json = [entity_to_json(entity) for entity in entities]
    print(entities_json)
    return entities_json