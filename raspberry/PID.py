
class PIDController:
    def __init__(self, Kp, Ki, Kd):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.previous_error = 0
        self.integral = 0

    def compute(self, setpoint, measurement):
        error = setpoint - measurement
        self.integral += error
        derivative = error - self.previous_error
        output = (self.Kp * error) + (self.Ki * self.integral) + \
            (self.Kd * derivative)
        self.previous_error = error
        return output
