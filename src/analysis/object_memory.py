class ObjectMemory:

    def __init__(self):
        self.store = {}

    def update(self, obj_id, label, bbox, zone, timestamp):

        if obj_id not in self.store:

            self.store[obj_id] = {
                "id": obj_id,
                "label": label,
                "bbox": bbox,
                "zone": zone,
                "first_seen": timestamp,
                "last_seen": timestamp,
                "count": 1
            }

        else:

            obj = self.store[obj_id]

            obj["bbox"] = bbox
            obj["zone"] = zone
            obj["last_seen"] = timestamp
            obj["count"] += 1

    def get(self, obj_id):
        return self.store.get(obj_id, None)

    def get_all(self):
        return self.store

    def remove(self, obj_id):
        if obj_id in self.store:
            del self.store[obj_id]
    