from random import randint
from collections import Counter
import numpy as np

class Device:
    def __init__(self, name, backoff_strategy='linear', backoff_param=None):
        self.stats = {}
        self.window = 1
        self.num_trial = 1
        self.name = name
        self.waiting_to_acquire = True
        self.total_wait_time = 0
        self.set_wait_time()

        self.backoff_strategy = backoff_strategy
        self.backoff_param = backoff_param
        if backoff_param is None:
            if self.backoff_strategy == "linear":
                self.backoff_param = 1
            elif self.backoff_strategy == "exponential":
                self.backoff_param = 2
            elif self.backoff_strategy == "polynomial":
                self.backoff_param = 2
            elif self.backoff_strategy == "backoff-backon":
                self.backoff_param = 1

    def set_wait_time(self):
        self.wait_time = randint(0, self.window-1)
        self.total_wait_time += self.wait_time
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
                self.increase_window_size()
                self.num_trial += 1
                self.set_wait_time()
                self.tick()
        return try_acquire                

    def acquire_success(self, timestamp):
        print(f"{self.name} has successfully acquired the resource at time {timestamp}, after {self.num_trial} tries")
        self.log_stats(timestamp)

    def acquire_fail(self, timestamp):
        # print(f"{self.name} has failed to acquired the resource at time {timestamp}")
        self.current_wait_time = self.window - self.wait_time - 1
        self.total_wait_time += self.current_wait_time
        self.waiting_to_acquire = False

    def log_stats(self, timestamp):
        stats = {"finish_time": timestamp,
                 "num_trial": self.num_trial,
                 "total_wait_time": self.wait_time}
        self.stats = stats

    def increase_window_size(self):
        if self.backoff_strategy == 'linear':
            self.window += self.backoff_param
        elif self.backoff_strategy == "exponential":
            self.window = self.backoff_param * self.window
        elif self.backoff_strategy == "polynomial":
            self.window = (self.num_trial + 1) ** self.backoff_param
        elif self.backoff_strategy == "backoff-backon":
            if self.window == 1:
                self.window = 2 ** self.backoff_param
                self.backoff_param += 1
            else:
                self.window /= 2
        


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
    def __init__(self, arrival_model, num_arrivals, backoff_strategy, backoff_params):
        self.device_list = {}
        self.stat_collection = []
        self.timestamp = 0
        self.resource = Resource()
        self.backoff_strategy = backoff_strategy
        self.backoff_params = backoff_params
        self.arrival_model = arrival_model
        self.num_arrivals = num_arrivals

    def add_devices(self):
        if self.num_arrivals == 0:
            return 

        num = self.arrival_model()
        for i in range(num):
            device_name = f"device{len(self.device_list)}"
            self.device_list[device_name] = Device(device_name, self.backoff_strategy, self.backoff_params)
        self.num_arrivals -= 1

    def tick(self):
        for device in self.device_list.values():
            if device.tick():
                self.resource.request_access(device)
        
        device_name = self.resource.tick()
        if device_name:
            self.stat_collection.append(self.device_list.pop(device_name, None))
        self.timestamp += 1

    def run(self):
        self.add_devices()
        while self.device_list or self.num_arrivals:
            self.tick()
            self.add_devices()
        self.report()

    def report(self):
        result = Counter()
        result["finish_time"] = self.timestamp - 1
        print()
        
        for device in self.stat_collection:
            finish_time = device.stats["finish_time"]
            num_trial = device.stats["num_trial"]
            total_wait_time = device.stats["total_wait_time"]
            avg_wait_time = total_wait_time / num_trial

            print(f"{device.name}: ")
            print(f"Finish time: {finish_time}")
            print(f"Number of trials: {num_trial}")
            print(f"Avg wait time: {avg_wait_time}")
            print()

            result["avg_num_trial"] += num_trial
            result["avg_finish_time"] += finish_time

        result["avg_num_trial"] /= len(self.stat_collection)
        result["avg_finish_time"] /=len(self.stat_collection)
        
        print(f"Number of devices: {len(self.stat_collection)}")
        print(f"Finish time: {result['finish_time']}")
        print(f"Average number of trial per device: {result['avg_num_trial']}")
        print(f"Average finish time per device is {result['avg_finish_time']}")
        

def constant_arrival(param):
    def arrival():
        return param
    return arrival

def gaussian_arrival(mean, std):
    def arrival():
        return int(np.random.normal(mean, std))
    return arrival

def poisson_arrival(param):
    def arrival():
        return np.random.poisson(param)
    return arrival

def uniform_arrival(param):
    def arrival():
        p = np.random.uniform()
        return 1 if p < param else 0
    return arrival

def bursty_arrival():
    return int(1 / np.random.uniform())


if __name__ == "__main__":
    sim = BackoffSimulation(gaussian_arrival(5, 2), 10, "backoff-backon", 1)
    sim.run()

