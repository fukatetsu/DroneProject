from djitellopy import Tello

class TelloController:

    def __init__(self):
        self.tello = Tello()

    def connect(self):
        self.tello.connect()
        print(f"Battery: {self.tello.get_battery()}%")

    def takeoff(self):
        self.tello.takeoff()

    def land(self):
        self.tello.land()