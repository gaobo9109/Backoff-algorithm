from random import randint
from collections import Counter

class Device:
    def __init__(self, name, backoff_strategy='linear', backoff_param=None):
        self.stats = {}
        self.window = 1
        self.num_trial = 1
        self.name = name
        self.waiting_to_acquire = True
        self.set_wait_time()
        self.backoff_strategy = backoff_strategy
        self.backoff_param = backoff_param
        if backoff_param is None:
            if self.backoff_strategy == "linear":
                self.backoff_param = 1
            elif self.backoff_strategy == "exponential":
                self.backoff_param = 2

    def set_wait_time(self):
        self.wait_time = randint(1, self.window)
        self.current_wait_time = self.wait_time

    def tick(self):
        try_acquire = False
        if self.current_wait_time > 0:
            self.current_wait_time -= 1
        else:
            if self.waiting_to_acquire:
                try_acquire = True
            else:
                self.waiting_to_acquire = True
                self.num_trial += 1
                self.increase_window_size()
                self.set_wait_time()
                try_acquire = self.tick()
        return try_acquire                

    def acquire_success(self, timestamp):
        print(f"{self.name} has successfully acquired the resource at time {timestamp}, after {self.num_trial} tries")
        self.log_stats(timestamp)

    def acquire_fail(self, timestamp):
        # print(f"{self.name} has failed to acquired the resource at time {timestamp}")
        self.current_wait_time = self.window - self.wait_time
        self.waiting_to_acquire = False

    def log_stats(self, timestamp):
        stats = {"finish_time": timestamp,
                 "num trial": self.num_trial,
                 "window size": self.window,
                 "wait time": self.wait_time}
        self.stats = stats

    def increase_window_size(self):
        if self.backoff_strategy == 'linear':
            self.window += self.backoff_param
        elif self.backoff_strategy == "exponential":
            self.window = self.backoff_param * self.window
        # elif self.backoff_strategy == "log":
        #     pass
        


class Resource:
    def __init__(self):
        self.timestamp = 0
        self.request_list = []

    def request_access(self, device):
        self.request_list.append(device)

    def tick(self):
        acquired_by = None
        if len(self.request_list) == 1:
            self.request_list[0].acquire_success(self.timestamp)
            acquired_by = self.request_list[0].name
        elif len(self.request_list) > 1:
            for device in self.request_list:
                device.acquire_fail(self.timestamp)

        self.request_list = []
        self.timestamp += 1
        return acquired_by


class BackoffSimulation:
    def __init__(self, num):
        self.device_list = {}
        self.stat_collection = []
        self.init_devices(num)
        self.timestamp = 0
        self.resource = Resource()

    def init_devices(self, num):
        for i in range(num):
            device_name = f"device{i}"
            self.device_list[device_name] = Device(device_name, "exponential", 2)

    def tick(self):
        for device in self.device_list.values():
            if device.tick():
                self.resource.request_access(device)
        
        device_name = self.resource.tick()
        if device_name:
            self.stat_collection.append(self.device_list.pop(device_name, None))
        self.timestamp += 1

    def run(self):
        while self.device_list:
            self.tick()
        self.report()

    def report(self):
        result = Counter()
        result = {"finish time": self.timestamp}
        
        for device in self.stat_collection:
            result["avg_num_trial"] += device.stats["num trial"]

        result["avg_num_trial"] /= len(self.stat_collection)
        print(f"Finish time: {result['finish time']}")
        print(f"Average number of trial per device: {result['avg_num_trial']}")
        


if __name__ == "__main__":
    sim = BackoffSimulation(10)
    sim.run()

