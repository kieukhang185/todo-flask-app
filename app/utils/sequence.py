from ..extensions import mongo

def get_next_sequence(name):
    seq = mongo.db.counters.find_one_and_update(
        {'_id': name},
        {'$inc': {'seq': 1}},
        upsert=True,
        return_document=True
    )
    return seq['seq']