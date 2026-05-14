class ObjectMemory:
    def __init__(self):
        self.memory = {}

    def update(self, obj_id, label, zone):
        if obj_id == -1:
            return None

        prev = self.memory.get(obj_id)

        self.memory[obj_id] = {
            "label": label,
            "zone": zone
        }

        return prev

    def get_movement(self, obj_id, current_zone):
        prev = self.memory.get(obj_id)

        if not prev:
            return "NEW"

        if prev["zone"] == current_zone:
            return "STABLE"

        return f"{prev['zone']} -> {current_zone}"